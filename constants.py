abi = [
      {
        "anonymous": False,
        "inputs": [
          {
            "indexed": True,
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "indexed": True,
            "internalType": "address",
            "name": "owner",
            "type": "address"
          }
        ],
        "name": "CameraAdded",
        "type": "event"
      },
      {
        "anonymous": False,
        "inputs": [
          {
            "indexed": True,
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "indexed": False,
            "internalType": "uint256",
            "name": "date",
            "type": "uint256"
          },
          {
            "indexed": False,
            "internalType": "string",
            "name": "connectionLoss",
            "type": "string"
          },
          {
            "indexed": False,
            "internalType": "uint256",
            "name": "totalLossPerDay",
            "type": "uint256"
          }
        ],
        "name": "ConnectionLossAdded",
        "type": "event"
      },
      {
        "anonymous": False,
        "inputs": [
          {
            "indexed": True,
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "indexed": False,
            "internalType": "string",
            "name": "videoHash",
            "type": "string"
          },
          {
            "indexed": False,
            "internalType": "uint256",
            "name": "date",
            "type": "uint256"
          },
          {
            "indexed": False,
            "internalType": "string",
            "name": "timeDesciption",
            "type": "string"
          }
        ],
        "name": "VideoAdded",
        "type": "event"
      },
      {
        "inputs": [],
        "name": "addCamera",
        "outputs": [
          {
            "internalType": "uint256",
            "name": "",
            "type": "uint256"
          }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "date",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "connectionLoss",
            "type": "string"
          },
          {
            "internalType": "uint256",
            "name": "totalLossPerDay",
            "type": "uint256"
          }
        ],
        "name": "addConnectionLoss",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "videoHash",
            "type": "string"
          },
          {
            "internalType": "uint256",
            "name": "date",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "timeDesciption",
            "type": "string"
          }
        ],
        "name": "addVideo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
      },
      {
        "inputs": [],
        "name": "cameraCount",
        "outputs": [
          {
            "internalType": "uint256",
            "name": "",
            "type": "uint256"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "",
            "type": "uint256"
          }
        ],
        "name": "cameras",
        "outputs": [
          {
            "internalType": "address",
            "name": "owner",
            "type": "address"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          }
        ],
        "name": "getCamera",
        "outputs": [
          {
            "internalType": "address",
            "name": "",
            "type": "address"
          },
          {
            "components": [
              {
                "internalType": "string",
                "name": "hash",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "timeDesciption",
                "type": "string"
              }
            ],
            "internalType": "struct VideoHashContract.Video[]",
            "name": "",
            "type": "tuple[]"
          },
          {
            "components": [
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "connectionLoss",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "totalLossPerDay",
                "type": "uint256"
              }
            ],
            "internalType": "struct VideoHashContract.ConnectionLoss[]",
            "name": "",
            "type": "tuple[]"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          }
        ],
        "name": "getConnectionLossByCamera",
        "outputs": [
          {
            "components": [
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "connectionLoss",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "totalLossPerDay",
                "type": "uint256"
              }
            ],
            "internalType": "struct VideoHashContract.ConnectionLoss[]",
            "name": "",
            "type": "tuple[]"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "startTime",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "endTime",
            "type": "uint256"
          }
        ],
        "name": "getConnectionLossByDateRange",
        "outputs": [
          {
            "components": [
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "connectionLoss",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "totalLossPerDay",
                "type": "uint256"
              }
            ],
            "internalType": "struct VideoHashContract.ConnectionLoss[]",
            "name": "",
            "type": "tuple[]"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          }
        ],
        "name": "getVideosByCamera",
        "outputs": [
          {
            "components": [
              {
                "internalType": "string",
                "name": "hash",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "timeDesciption",
                "type": "string"
              }
            ],
            "internalType": "struct VideoHashContract.Video[]",
            "name": "",
            "type": "tuple[]"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {
            "internalType": "uint256",
            "name": "cameraId",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "startTime",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "endTime",
            "type": "uint256"
          }
        ],
        "name": "getVideosByDateRange",
        "outputs": [
          {
            "components": [
              {
                "internalType": "string",
                "name": "hash",
                "type": "string"
              },
              {
                "internalType": "uint256",
                "name": "date",
                "type": "uint256"
              },
              {
                "internalType": "string",
                "name": "timeDesciption",
                "type": "string"
              }
            ],
            "internalType": "struct VideoHashContract.Video[]",
            "name": "",
            "type": "tuple[]"
          }
        ],
        "stateMutability": "view",
        "type": "function"
      }
    ]