# condedrive
Onedrive synchronization client on GNU/Linux systems (alpha version)

Features:  

- Two-way synchronization (Local <-> Onedrive)  
- SQLite for database  
- File config  
- Mirroring rules  
- Upload/Download rules  
- Log info and debug  
- Sending files larger than 100mb with informative  

Dependencies:  

- python 3.X  
- onedrivesdk  
- pillow  
- requests  

Instructions:

- Register APP in your MS Account: https://dev.onedrive.com/app-registration.htm  
- Set your CLIENT_ID and CLIENT_SECRET in condedrive.conf  
- Execute python conde.py  
- Paste url in browser and cut return code.. paste in console  

API DOC: https://jslabs.cc/condedrive/doc/index.html