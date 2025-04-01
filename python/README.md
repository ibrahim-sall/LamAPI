# General

Open AR Cloud GeoPoseProtocol Python implementation

Created based on the protocol definition: https://github.com/OpenArCloud/oscp-geopose-protocol

Created by Gabor Soros, Nokia Bell Labs, 2023
Copyright Nokia
MIT License


# Python environment for testing
```
conda create -n oscp_test
conda activate oscp_test
conda install -c anaconda requests
conda install -c anaconda flask
conda install -c anaconda pillow
```

# Running on Windows
Start the server: `run-oscp-gpp-server.cmd`. You can test whether the server is running by typing in your browser: `http://localhost:8080/geopose`

Start the client and execute a single request: `run-oscp-gpp-client.cmd`

# Running on Linux
Similar to Windows but run the Shell scripts.

# Add a html page to make the requests more easily 
 run '''bash 
 python client.py
 ''' 
 and access to localhost webpage to make the request with one click on the button

 WARNING Everything is on the local where client.py is running so not good for production.
