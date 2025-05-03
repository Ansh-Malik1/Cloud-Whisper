import streamlit as st
import requests
from openstack import connection
import json
import openstack
import pandas as pd
import csv

# Initialize OpenStack connection
conn = connection.Connection(
    region_name='ap-south-mum-1',
    auth=dict(
        auth_url='https://api-ap-south-mum-1.openstack.acecloudhosting.com:5000/v3',
        username='Hackathon_AIML_1',
        password='Hackathon_AIML_1@567',
    ),
    compute_api_version='2',
    identity_interface='internal',
    user_domain_name='Default',  # ← REQUIRED
    project_domain_name='Default',
    endpoint_override={
        'compute': 'https://api-ap-south-mum-1.openstack.acecloudhosting.com:8774/v2.1',
        'image': 'https://api-ap-south-mum-1.openstack.acecloudhosting.com:9292'
    }
)

# Function to run API
def run_api(prompt=None, file=None):
    try:
        url = "http://127.0.0.1:8000/Speech_input_file"
        params = {
            "prompt": prompt
        }
        files = []
        response = requests.post(
            url,
            files=files,
            data=params
        )
        print(response.text)
        api_data = response.text
        return api_data
    except Exception as e:
        print("failed")
        return str(e)

# Function to create a virtual machine
def create_vm(vm_name, flavour="C.4", network='External_Net_MUM', image="Ubuntu-24.04", size=60):
    st.write(f"Creating a Virtual Machine with Image : {image}, VM name: {vm_name}, flavour:{flavour}, network : {network}, Size : {size}")
    image = conn.compute.find_image(image)
    flavor = conn.compute.find_flavor(flavour)
    network = conn.network.find_network(network)
    boot_volume = conn.block_storage.create_volume(
        size=size,  # GB; ensure it's large enough
        name='boot-volume',
        image_id=image.id
    )
    conn.block_storage.wait_for_status(boot_volume, status='available')
    server = conn.compute.create_server(
        name=vm_name,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        block_device_mapping_v2=[
            {
                'boot_index': 0,
                'uuid': boot_volume.id,
                'source_type': 'volume',
                'destination_type': 'volume',
                'delete_on_termination': True
            }
        ]
    )
    server = conn.compute.wait_for_server(server)
    st.write(f"Server '{server.name}' is ACTIVE with ID {server.id}")
    return server.id

# Function to resize a VM
# def vm_resizing(name, flavour):
#     server = conn.compute.find_server(name)
#     if server is None:
#         st.error("Server not found")
#         return
#     new_flavor = conn.compute.find_flavor(flavour)
#     if new_flavor is None:
#         st.error(f"Flavor {flavour} not found")
#         return
#     st.write(f"Resizing server '{server.name}' to flavor '{new_flavor.name}'...")
#     conn.compute.resize_server(server, new_flavor.id)
#     server = conn.compute.wait_for_server(server, status='VERIFY_RESIZE')
#     conn.compute.confirm_server_resize(server)
#     st.write(f"Resize confirmed for server '{server.name}'. Done!")

# # Function to delete a VM
# # def deletion(vm_name):
#     if vm_name is None:
#         st.error("Server not found")
#         return
#     server = conn.compute.find_server(vm_name)
#     if not server:
#         st.error(f"Error: Server '{vm_name}' not found")
#         return
#     if server.os_extended_volumes.volumes_attached:
#         for volume in server.os_extended_volumes.volumes_attached:
#             volume_id = volume['id']
#             st.write(f"Detaching volume: {volume_id}")
#             conn.compute.detach_volume(server, volume_id)
#     if server.status == 'ACTIVE':
#         st.write(f"Stopping server '{server.name}'...")
#         conn.compute.stop_server(server)
#         server = conn.compute.get_server(server.id)  # Refresh server object to get updated status
#         conn.compute.wait_for_server(server, status='SHUTOFF')
#         st.write(f"Server '{server.name}' is now stopped.")
#     st.write(f"Deleting server '{server.name}'...")
#     conn.compute.delete_server(server.id)
#     try:
#         server = conn.compute.get_server(server.id)  # Refresh server object
#         conn.compute.wait_for_server(server, wait=30, status='DELETED')
#         st.write(f"Server '{server.name}' has been deleted.")
#     except openstack.exceptions.ResourceNotFound:
#         st.write(f"Server '{server.name}' is already deleted.")
#     except Exception as e:
#         st.error(f"Error while waiting for deletion: {e}")


def vm_resizing(name,flavour):
    print(name)
    server = conn.compute.find_server(name)
    flavors = conn.compute.flavors()
    for flavor in flavors:
        print(f"Flavor ID: {flavor.id}, Name: {flavor.name}")
    if server is None:
        print("Server not found")
        exit(1)
        

    # Find the new flavor
    new_flavor = conn.compute.find_flavor(flavour)
    if new_flavor is None:
        print(f"Flavor {flavour} not found")
        exit(1)
        # break

    # Check current status
    server = conn.compute.get_server(server.id)
    st.write(f"Server '{server.name}' status: {server.status}")

    if server.status == 'VERIFY_RESIZE':
        st.write(f"Server is in VERIFY_RESIZE — confirming pending resize...")
        conn.compute.revert_server_resize(server)
        server = conn.compute.get_server(server.id)
        st.write(f"Resize reverted. Status now: {server.status}")

    # Now proceed with new resize
    st.write(f"Resizing server '{server.name}' to flavor '{new_flavor.name}'...")
    conn.compute.resize_server(server, new_flavor.id)

    # Wait and confirm as usual
    server = conn.compute.wait_for_server(server, status='VERIFY_RESIZE')
    st.write(f"Server '{server.name}' is now in VERIFY_RESIZE state.")
    conn.compute.confirm_server_resize(server)
    st.write(f"Resize confirmed for server '{server.name}'. Done!")
def deletion(vm_name,):
    
    if vm_name is None:
        print("Server not found")
        exit(1)
    server = conn.compute.find_server(vm_name)
    if not server:
        print(f"Error: Server '{vm_name}' not found")
        exit(1)

    # Check if there are attached volumes
    # if server.os_extended_volumes.volumes_attached:
    #     print("Server has attached volumes. Detaching volumes before deletion...")
    #     for volume in server.os_extended_volumes.volumes_attached:
    #         volume_id = volume['id']
    #         print(f"Detaching volume: {volume_id}")
    #         conn.compute.detach_volume(server, volume_id)

    # Stop the server if it's in the ACTIVE state
    if server.status == 'ACTIVE':
        print(f"Server is currently ACTIVE. Stopping server '{server.name}'...")
        conn.compute.stop_server(server)
        # Wait for the server to stop
        server = conn.compute.get_server(server.id)  # Refresh server object to get updated status
        conn.compute.wait_for_server(server, status='SHUTOFF')
        print(f"Server '{server.name}' is now stopped.")

    # Delete the server
    st.write(f"Deleting server '{server.name}'...")
    conn.compute.delete_server(server.id)

    # Optionally, wait for the server to be deleted
    try:
        server = conn.compute.get_server(server.id)  # Refresh server object
        conn.compute.wait_for_server(server, wait=30, status='DELETED')
        st.write(f"Server '{server.name}' has been deleted.")
    except openstack.exceptions.ResourceNotFound:
        st.write(f"Server '{server.name}' is already deleted.")
    except Exception as e:
        st.write(f"Error while waiting for deletion: {e}")



# Function to create a network
def create_network(network_name, subnet_name=""):
    network_name = network_name
    subnet_name = network_name + "subnet"
    cidr = '192.168.1.0/24'
    network = conn.network.create_network(name=network_name)
    st.write(f"Network '{network_name}' created with ID: {network.id}")
    subnet = conn.network.create_subnet(
        name=subnet_name,
        network_id=network.id,
        ip_version=4,  # IPv4
        cidr=cidr,
        gateway_ip='192.168.1.1'  # Set the gateway IP address for the subnet
    )
    st.write(f"Subnet '{subnet.name}' created with CIDR: {cidr} on network '{network_name}'")

# Function to create a volume
def create_volume(size, name):
    print("inside create_volume")
    volume = conn.block_storage.create_volume(
        name=name,
        size=size
    )
    st.write(f"Volume '{volume.name}' created with ID: {volume.id}")

# Function to delete a volume
def delete_volume(volume_name):

    volume = conn.block_storage.find_volume(volume_name)
    if volume:
        if volume.status == 'in-use':
            st.error(f"Volume '{volume_name}' is still attached; detach it before deletion.")
        else:
            conn.block_storage.delete_volume(volume, ignore_missing=False)
            st.write(f"Deleted volume '{volume_name}' successfully.")
    else:
        st.error(f"Volume '{volume_name}' not found.")

# def write_in_csv(user_name,operation,vm_name,network,image,size,flavour):
#     d = {
#         'user_name': user_name,
#         'operation': operation,
#         'vm_name': vm_name,
#         'network': network,
#         'image': image,
#         'size': size,
#         'flavour': flavour
#     }

#     # Path to the uploaded CSV file
#     file_path = 'database.csv'

#     # Append to CSV file
#     with open(file_path, 'a', newline='') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=d.keys())
        
#         # Write header if file is empty
#         csvfile.seek(0)
#         if not csvfile.read(1):
#             writer.writeheader()
        
#         writer.writerow(d)

#     print("Row added to the CSV.")

import csv
import os

def write_in_csv(user_name, operation, vm_name, network, image, size, flavour):
    d = {
        'user_name': user_name,
        'operation': operation,
        'vm_name': vm_name,
        'network': network,
        'image': image,
        'size': size,
        'flavour': flavour
    }

    file_path = 'database.csv'

    # Check if file exists and is empty
    file_exists = os.path.exists(file_path)
    is_empty = os.path.getsize(file_path) == 0 if file_exists else True

    # Append to the file
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=d.keys())
        
        if is_empty:
            writer.writeheader()  # Only write headers if file is empty
        
        writer.writerow(d)  # Always writes to the next line

    print("Row successfully appended.")


# Function to handle main logic
def main_func(prompt=None, file=None,user_name=None):
    
    # df=pd.read_csv("database.csv")

    response = run_api(prompt, file)
    responses = json.loads(response)
    st.markdown(responses["response"])
    response_json = responses["json_outputs"]
    response_json1 = response_json.replace("\\", "")
    response_json = json.loads(response_json1)
    operation = response_json["Operation"]
    flavour = response_json["Flavor"]
    Name = response_json["Name"]
    resource_type = response_json["Resource Type"]
    try:
        size=response_json["size"]
    except:
        size=60
    try:
        image=response_json["image"]
    except:
        image="Ubuntu-24.04"
    try:
        network=response_json["network"]
    except:
        network="External_Net_MUM"

    if network=="" or network=={} or network=="{}":
        # flavour="C.4",network='External_Net_MUM',image="'Ubuntu-24.04'",size=20
        network="External_Net_MUM"
    if Name=="" or Name=={} or Name=="{}":
        Name="test-vm"
    
    if size==""or size=={} or size==0 or size=="{}":
        size=60
    if image=="" or image=={} or image==None or image=="{}":
        image="Ubuntu-24.04"

    if operation == "Create VM":
        # but = st.button("Are You Sure You Want to Create the vm")
        # if but:
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)

        create_vm(vm_name=Name, flavour=flavour, network=network, image=image, size=size)
        
    elif operation == "Resize":
        # but = st.button("Are You Sure You Want to resize the vm")
        # if but:
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)


        vm_resizing(name=Name, flavour=flavour)
    elif operation == "Delete":
        # but = st.button("Are You Sure You Want to Delete  the vm")
        # if but:
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)
        
        deletion(Name)
    elif operation == "Network Creation":
        # but = st.button("Are You Sure You Want to Create Network")
        # if but:
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)

        create_network(Name)
    elif operation == 'Volume Create' or operation=="Create Volume":
        # if st.button("Are You Sure You Want to Create volume"):
        st.warning("You are creating a volume")
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)

        create_volume(size, Name)
    elif operation == 'Delete Volume':
        # but = st.button("Are You Sure You Want to delete the vol")
        # if but:
        write_in_csv(user_name,operation,vm_name=Name,network=network,image=image,size=size,flavour=flavour)
        delete_volume(Name)
    

# Streamlit App
# st.title("Cloud Whisper")
icon_path = './logo .png'
st.set_page_config(page_title="Cloud Whisper",
                    layout='centered')
_, logo, _ = st.columns(3)
logo.image(icon_path, width=200)
style = ("text-align:center; padding: 0px; font-family: arial black;, "
            "font-size: 400%")
title = f"<h1 style='{style}'>Cloud Whisper<sup></sup></h1><br><br>"
st.write(title, unsafe_allow_html=True)

# Ask for user's name
user_name = st.text_input("Please enter your name:")
if user_name:
    st.write(f"Welcome, {user_name}!")

# Input for prompt or file
prompt = st.text_area("Enter the operation prompt:")
# file = st.file_uploader("Upload a file (optional):")

# Run main function on button click
if st.button("Submit"):
    main_func(prompt=prompt, file=[],user_name=user_name)