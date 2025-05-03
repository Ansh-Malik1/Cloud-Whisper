Cloud whisper is a smart-new age AI event that takes away all the burden of performing various cloud operations. It is a streamlit based webapp wherein the user can write any command for cloud operation like ‘Create a S.4 VM named test-cloud’. The agent will the process the text input given by the user using NLP and then calls Openstack API to create a VM named ‘test-cloud’ with flavor as ‘S.4’.
Video Link : https://www.loom.com/share/0033c0f44a1c4303ab4ce7589f735998?sid=197c3a10-be4d-4b0b-8faf-a2d8a34d7912
<br><br><br>
To run this locally, install all the dependencies written in requirements.txt
'pip install -r requirements.txt'

Then run the following command : 
streamlit run streamlit_app.py
