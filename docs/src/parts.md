# Parts

Because the RLG G1 Face was modeled using [Onshape](https://www.onshape.com/en/), a
cloud-native CAD platform, the model may be freely viewed [here](https://cad.onshape.com/documents/0979ae98021520f5b9b15ec4/w/0da676341647822235e1b00c/e/b5aea366bc62dd84a894a42c?renderMode=0&uiState=6ac84a18cda8da631e06378a).

Most parts are 3D printed, so you will first need to download the CAD files.
Thanks to the fact that Onshape is cloud-based and exposes a convenient REST API,
there is a script for automatically downloading and updated the .step models.
The script is located at `cad/download_model.py`.

## Running the script

To use the download script, you will need to have `python` and `uv` installed. If
you don't have python installed, there are various guides on how to get
it installed such as [this one](https://wiki.python.org/moin/BeginnersGuide(2f)Download.html).

Once python is installed, installing `uv` is simple. See [here](https://docs.astral.sh/uv/getting-started/installation/).

Next, you will need to [create your API keys](https://onshape-public.github.io/docs/api-intro/quickstart/#3-create-your-api-keys) and store them in `cad/secrets.yaml`. A template is provided at `cad/secrets.example.yaml`.

Finally, to run the download script, change directory into the `cad` and
run 

```bash
uv sync
uv run download-model
```
