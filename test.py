import requests
import openstack
from openstack import connection
import json
def run_api(prompt=None,file=None):
    try :
        url="http://127.0.0.1:8000/Speech_input_file"
        params={
            # "prompt":"Create an S.4 VM named dev-box."
            "prompt":prompt

        }
        # resp=requests.post(url=url,params=params)
        # print(resp)
        if file==None:
            files=[]
        else :
            files=[]
        response = requests.post(
            url,
            files=files,
            data=params
        )
        print(response.text)
        api_data=response.text
        return api_data
    except Exception as e :
        print("failed")
        return e
    

conn = connection.Connection(
    region_name='ap-south-mum-1',
    auth=dict(
        auth_url='https://api-ap-south-mum-1.openstack.acecloudhosting.com:5000/v3',
        username='Hackathon_AIML_1',
        password='Hackathon_AIML_1@567',),
    compute_api_version='2',
    identity_interface='internal',
    user_domain_name='Default',        # ← REQUIRED
    project_domain_name='Default',
    endpoint_override={
        'compute':'https://api-ap-south-mum-1.openstack.acecloudhosting.com:8774/v2.1',
        'image':'https://api-ap-south-mum-1.openstack.acecloudhosting.com:9292'
    }
    )
def create_vm(vm_name,flavour="C.4",network='External_Net_MUM',image="Ubuntu-24.04",size=60):
    print(f"Creating a Virtual Machine with Image : {image}, VM name: {vm_name}, flavour:{flavour},network : {network}, Size : {size} ")
    image = conn.compute.find_image('Ubuntu-24.04')
    flavor = conn.compute.find_flavor('C.4')
    network = conn.network.find_network('External_Net_MUM')
    boot_volume = conn.block_storage.create_volume(
        size=60,  # GB; ensure it's large enough
        name='boot-volume',
        image_id=image.id
    )

    # Wait until volume is ready
    conn.block_storage.wait_for_status(boot_volume, status='available')

    # Launch server booting from the volume
    server = conn.compute.create_server(
        name=vm_name,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        block_device_mapping_v2=[{
            'boot_index': 0,
            'uuid': boot_volume.id,
            'source_type': 'volume',
            'destination_type': 'volume',
            'delete_on_termination': True
        }]
    )

    # Wait for the server to become ACTIVE
    server = conn.compute.wait_for_server(server)
    print(f"Server '{server.name}' is ACTIVE with ID {server.id}")
    return server.id

def vm_resizing(name,flavour):
    print(name)
    server = conn.compute.find_server(name)
    flavors = conn.compute.flavors()
    for flavor in flavors:
        print(f"Flavor ID: {flavor.id}, Name: {flavor.name}")
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
    print(f"Server '{server.name}' status: {server.status}")

    if server.status == 'VERIFY_RESIZE':
        print(f"Server is in VERIFY_RESIZE — confirming pending resize...")
        conn.compute.revert_server_resize(server)
        server = conn.compute.get_server(server.id)
        print(f"Resize reverted. Status now: {server.status}")

    # Now proceed with new resize
    print(f"Resizing server '{server.name}' to flavor '{new_flavor.name}'...")
    conn.compute.resize_server(server, new_flavor.id)

    # Wait and confirm as usual
    server = conn.compute.wait_for_server(server, status='VERIFY_RESIZE')
    print(f"Server '{server.name}' is now in VERIFY_RESIZE state.")
    conn.compute.confirm_server_resize(server)
    print(f"Resize confirmed for server '{server.name}'. Done!")


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
    print(f"Deleting server '{server.name}'...")
    conn.compute.delete_server(server.id)

    # Optionally, wait for the server to be deleted
    try:
        server = conn.compute.get_server(server.id)  # Refresh server object
        conn.compute.wait_for_server(server, wait=30, status='DELETED')
        print(f"Server '{server.name}' has been deleted.")
    except openstack.exceptions.ResourceNotFound:
        print(f"Server '{server.name}' is already deleted.")
    except Exception as e:
        print(f"Error while waiting for deletion: {e}")



def create_network(network_name,subnet_name=""):
    print("in create Network")
    network_name = network_name
    subnet_name = network_name+"subnet"
    cidr = '192.168.1.0/24'  

    # Create a network
    network = conn.network.create_network(name=network_name)
    print(f"Network '{network_name}' created with ID: {network.id}")

    # Create a subnet
    subnet = conn.network.create_subnet(
        name=subnet_name,
        network_id=network.id,
        ip_version=4,  # IPv4
        cidr=cidr,
        gateway_ip='192.168.1.1'  # Set the gateway IP address for the subnet
    )
    print(f"Subnet '{subnet.name}' created with CIDR: {cidr} on network '{network_name}'")

def create_volume(size,name):
    volume = conn.block_storage.create_volume(
    name=name,
    size=size
    )
    print(f"Volume '{volume.name}' created with ID: {volume.id}")
    
def delete_volume(volume_name):
    volume = conn.block_storage.find_volume(volume_name)

    if volume:
        # Check if the volume is attached (cannot delete if still attached)
        if volume.status == 'in-use':
            print(f"Volume '{volume_name}' is still attached; detach it before deletion.")
        else:
            conn.block_storage.delete_volume(volume, ignore_missing=False)
            print(f"Deleted volume '{volume_name}' successfully.")
    else:
        print(f"Volume '{volume_name}' not found.")

def main_func(prompt=None,file=None):
    response=run_api(prompt,file)
    responses=json.loads(response)
    response_json=responses["json_outputs"]
    response_json1=response_json.replace("\\","")
    
    # print(response_json1,type(response_json1))
    response_json=json.loads(response_json1)
    # response_json=dict(response_json)
    # print(response_json,type(response_json))

    operation=response_json["Operation"]
    flavour=response_json["Flavor"]
    Name=response_json["Name"]
    resource_type=response_json["Resource Type"]
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


    # print(resource_type,operation,flavour,Name,size,image,network)

    if network=="" or network=={}:
        # flavour="C.4",network='External_Net_MUM',image="'Ubuntu-24.04'",size=20
        network="External_Net_MUM"
    if Name=="" or Name=={}:
        Name="test-vm"
    
    if size==""or size=={}:
        size=60
    if image=="" or image=={}:
        image="Ubuntu-24.04"
    if operation=="Create VM":
        a=int(input("Do you want to create a Virtual Machine if yes enter 1:"))
        if a==1:
            create_vm(vm_name=Name,flavour=flavour,network=network,image=image,size=size)
    elif operation=="Resize":
        a=int(input("Do you want to Resize a Virtual Machine if yes enter 1:"))
        if a==1:
            vm_resizing(name=Name,flavour=flavour)
    elif operation=="Delete" or operation=="Delete VM":
        a=int(input("Do you want to Resize a Virtual Machine if yes enter 1:"))
        if a==1:
            deletion(Name)
    elif operation=="Network Creation":
        create_network(Name)
    elif operation=='Create Volume' or operation=="Volume Create":
        create_volume(size,Name)
    elif operation=='Delete Volume':
        delete_volume(Name)
    # elif operation=='Usage Query':
    #     usage_querry()


# main_func("Create an C.4 VM named acserver")
# main_func("Resize acserver to flavor C.96")
#main_func("Delete the VM acserver")
#main_func("Create a private network called green-net")
# main_func("Create a 10 GB volume named data‑disk.")
main_func("Delete the volume named data-disk")
