from .model_downloader import ModelDownloader, DocID, PropID, VerID

from typing import Any

from pathlib import Path
import os
import shutil

import yaml


def main():
    # load files
    config_file = Path('config.yaml')
    secrets_file = Path('secrets.yaml')

    with open(config_file, mode='r') as fconfig:
        config: dict[str, Any] = yaml.load(fconfig, Loader=yaml.Loader)
    with open(secrets_file, mode='r') as fsecrets:
        secrets: dict[str, str] = yaml.load(fsecrets, Loader=yaml.Loader)

    assert isinstance(config, dict), (
        'Config yaml file should be a dictionary! Is it broken?'
    )
    assert isinstance(secrets, dict), (
        'Secrets yaml file should be a dictionary! Is it broken?'
    )

    server: str = config['onshape_server']
    doc: DocID = config['document_id']
    export_id: PropID = config['export_property_id']
    workspace: None | VerID = (
        config['workspace_id'] if not config['use_default_workspace'] else None
    )
    dlpath = Path(config['dlpath'])

    # get from onshape
    downloader = ModelDownloader(
        server, secrets['access_key'], secrets['secret_key'], doc, export_id, workspace
    )
    downloader.get_and_download_models(dlpath)

    # recursively unzip files
    print('Download complete! Unzipping..')
    for file in os.listdir(dlpath):
        fname = os.fsdecode(file)
        if fname.endswith('.zip'):
            dl_zip_path = dlpath / fname
            dl_dir_path = dlpath / Path(fname.rstrip('.zip'))
            # clean old folder if present
            if os.path.exists(dl_dir_path):
                shutil.rmtree(dl_dir_path)
            print(f'Unzipping {fname}')
            shutil.unpack_archive(dl_zip_path, dl_dir_path)
            # remove zip file
            os.remove(dl_zip_path)

    print('Download completed successfully!')


if __name__ == '__main__':
    main()
