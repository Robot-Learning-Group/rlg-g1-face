"""
This is a script for automatically downloading .step models from OnShape

Set your API key in a neighboring `secrets.yaml` file
Config is located in a neighboring `config.yaml` file

Run it with uv: uv run download-model
"""

from time import sleep

import requests
from requests.adapters import Response
import json

# for parsing filename
from email.message import Message

from urllib.parse import urljoin

from pathlib import Path
from typing import TypeAlias, Literal

DocID: TypeAlias = str  # Document ID type
PropID: TypeAlias = str  # Property ID type
VerID: TypeAlias = str  # Workspace/version/microversion ID type
ElemID: TypeAlias = str  # Element ID type
PartID: TypeAlias = str  # Part ID type


class ModelDownloader:
    def __init__(
        self,
        server: str,
        access_key: str,
        secret_key: str,
        doc: DocID,
        export_id: PropID,
        workspace: None | VerID = None,
        wspace_type: str = 'w',
    ):
        self.server: str = server.rstrip('/') + '/'
        self.access_key: str = access_key
        self.secret_key: str = secret_key
        self.doc: DocID = doc
        self.export_id: PropID = export_id

        if workspace is None:
            self.workspace = self.get_default_workspace()
            self.workspace_type = 'w'
        else:
            self.workspace = (workspace,)
            self.workspace_type = wspace_type

    def _get_json_request(
        self,
        endpoint: str,
        params: dict = {},
        media_type: str = 'application/json;charset=UTF-8; qs=0.09',
    ) -> dict | list:
        """Send a GET request to the server."""
        res = requests.get(
            urljoin(self.server, endpoint),
            params=params,
            auth=(self.access_key, self.secret_key),
            headers={'Accept': media_type, 'Content-type': 'application/json'},
        )

        assert res.status_code == 200, (
            f'Request sent to {res.url} is not OK! '
            f'Got {res.status_code}. Response text: {res.text}'
        )

        return res.json()

    def _get_download_request(self, endpoint: str, dlpath: Path):
        """Download a file from the server"""
        res = requests.get(
            urljoin(self.server, endpoint),
            params={},
            auth=(self.access_key, self.secret_key),
            headers={
                'Accept': 'application/json;charset=UTF-8; qs=0.09',
                'Content-type': 'application/json',
            },
        )

        assert res.status_code == 200, (
            f'Request sent to {res.url} is not OK! '
            f'Got {res.status_code}. Response text: {res.text}'
        )

        # get filename
        msg = Message()
        msg['Content-Disposition'] = res.headers['content-disposition']

        filename = msg.get_filename()
        assert filename is not None
        dlpath.mkdir(parents=True, exist_ok=True)
        open(dlpath / Path(filename), 'wb').write(res.content)

    def _post_request(
        self,
        endpoint: str,
        body: dict,
        params: dict = {},
        media_type: str = 'application/json;charset=UTF-8; qs=0.09',
    ) -> dict:
        """Send a POST request to the server."""
        res = requests.post(
            urljoin(self.server, endpoint),
            json=body,
            params=params,
            auth=(self.access_key, self.secret_key),
            headers={'Accept': media_type, 'Content-type': 'application/json'},
        )

        assert res.status_code == 200, (
            f'Request sent to {res.url} is not OK! '
            f'Got {res.status_code}. Response text: {res.text}'
        )

        return res.json()

    def get_default_workspace(self) -> VerID:
        """Get the default workspace of the document"""
        endpoint = f'documents/{self.doc}'

        res = self._get_json_request(endpoint)
        assert isinstance(res, dict)
        return res['defaultWorkspace']['id']

    def get_part_studios(self) -> list[tuple[str, ElemID]]:
        """Get all part studios in the workspace"""
        endpoint = (
            f'documents/d/{self.doc}/{self.workspace_type}/{self.workspace}/elements'
        )

        res = self._get_json_request(endpoint)
        assert isinstance(res, list)

        return [
            (elem['name'], elem['id']) for elem in res if elem['type'] == 'Part Studio'
        ]

    def get_export_parts(self, part_studio: ElemID) -> list[tuple[str, PartID]]:
        """Get a list of parts in a partstudio which have the export property"""
        endpoint = (
            f'parts/d/{self.doc}/{self.workspace_type}/{self.workspace}/e/{part_studio}'
        )
        params = {'withThumbnails': False, 'includePropertyDefaults': True}

        res = self._get_json_request(endpoint, params=params)
        assert isinstance(res, list)

        return [
            (part['name'], part['partId'])
            for part in res
            if part['customProperties'][self.export_id] == 'true'
        ]

    def _download_models(
        self,
        part_studio: ElemID,
        name: str,
        parts: list[tuple[str, PartID]],
        dlpath: Path,
    ):
        endpoint = f'partstudios/d/{self.doc}/{self.workspace_type}/{self.workspace}/e/{part_studio}/export/step'
        print(endpoint)
        part_ids = [part[1] for part in parts]
        body = {
            'advancedParams': {
                'partIds': ','.join(part_ids),
            },
            'destination': f'{name}.zip',
            'grouping': False,
            'isYAxisUp': False,
            'stepUnit': 'METER',
            'stepVersionString': 'AP242',
            'storeInDocument': False,
        }

        res = self._post_request(endpoint, body)

        # poll and wait for download to finish
        endpoint = f'translations/{res["id"]}'
        status: Literal['ACTIVE', 'DONE', 'FAILED'] = res['requestState']
        while status == 'ACTIVE':
            print('Waiting for conversion..')
            sleep(4)
            res = self._get_json_request(endpoint)
            assert isinstance(res, dict)
            status = res['requestState']

        assert status == 'DONE', 'Conversion to STEP failed!'

        # download file
        for fid in res['resultExternalDataIds']:
            endpoint = f'documents/d/{self.doc}/externaldata/{fid}'
            self._get_download_request(endpoint, dlpath)

    def get_and_download_models(self, dlpath: Path):
        print('Fetching part studios..')
        part_studios = self.get_part_studios()
        for part_studio in part_studios:
            print(f'Found "{part_studio[0]}": {part_studio[1]}')

        print('Fetching parts..')
        for part_studio in part_studios:
            pstudio_name = part_studio[0]
            pstudio_id = part_studio[1]

            print(f'Searching {pstudio_name}')
            entries = self.get_export_parts(pstudio_id)

            if len(entries) == 0:
                print('Part studio has no files marked for download, skipping..')
                continue

            for entry in entries:
                print(f'Found "{entry[0]}": {entry[1]}')

            print('Downloading parts inside this part studio..')
            self._download_models(pstudio_id, pstudio_name, entries, dlpath)
