#!/bin/bash
echo "The set up script it running"
git clone https://github.com/SplitSky/resdata.git
sudo apt install uvicorn
pip install "fastapi[all]"
sudo apt install python
pip install pymongo
pip install python-jose
pip install cryptography
echo "The set up is complete."
