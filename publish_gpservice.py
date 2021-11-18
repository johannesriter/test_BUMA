import arcpy, json
import datetime, time
import os
import sys

from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

workspace = r'C:\Users\jrsitompul\Documents\ArcGIS\Projects\PersonalProject'

def get_KVvalue(name):
    credential = ClientSecretCredential(tenant_id='ae6627ad-4b20-466d-821c-fd9ee7a25a55', client_id='e0839339-e0ff-48a2-8eb7-6e1f83880708', client_secret='~__V7kS.aphhf2C3JBr8.Spo.93nVi7TlJ')
    client = SecretClient(vault_url='https://omine-dev-akv-001.vault.azure.net/', credential=credential)
    
    try:
        secret_bundle = client.get_secret(name)
        return secret_bundle.value
    except:
        print(sys.exc_info())
        return ''

class log_script():
    def log_info(message):
        now_time = datetime.datetime.today()
        time_str = datetime.datetime.strftime(now_time, "%d-%m-%Y %H:%M")
        concate_msg = "{} {}".format(time_str, message)
        arcpy.AddMessage(concate_msg)

class publish_GP():
    def create_GP_SD():

        # Sign in to Portal
        log_script.log_info('Connect to portal...')
        user = 'portaladmin' #'{}'.format(get_KVvalue('ArcGISEnterprise--username'))
        passw = 'PortalPSYOI' #'{}'.format(get_KVvalue('ArcGISEnterprise--password'))
        
        arcpy.SignInToPortal("https://ps.esriindonesia.co.id/portal", user, passw)
        server = r'https://ps.esriindonesia.co.id/server' # r'https://gisdev.bukitmakmur.com/arcgis/admin'

        # Input & Output file name
        gp_tool = r'C:\Users\jrsitompul\Documents\ArcGIS\Projects\PersonalProject\test_gp.tbx'
        service_name = "test_publish_gpservice"
        sddraft = service_name + ".sddraft"
        sddraft_output = os.path.join(workspace, sddraft)
        sd = service_name + ".sd"
        sd_output = os.path.join(workspace, sd)

        # Run the tool and set result
        log_script.log_info('Running GP tool...')
        arcpy.ImportToolbox(gp_tool)
        result = arcpy.testgp.testgp()
        log_script.log_info('GP tool runs successfully.')

        # Create service definition draft and return analyzer messages
        analyzeMessages = arcpy.CreateGPSDDraft(result, sddraft_output, service_name, server_type="MY_HOSTED_SERVICES", copy_data_to_server=True, folder_name=None, summary="Test GP service", tags="gp", executionType="Asynchronous", resultMapServer=False, showMessages="INFO", maximumRecords=2000, minInstances=2, maxInstances=3, maxUsageTime=300, maxWaitTime=60, maxIdleTime=1800)
        log_script.log_info('Success to create GP Draft file.')

        # Delete previous SD file
        if os.path.exists(sd_output):
            os.remove(sd_output)
        else:
            log_script.log_info("The {} file doesn't exist.".format(sd))

        # Stage and upload the service if the sddraft analysis did not
        # contain errors
        if analyzeMessages['errors'] == {}:
            # Execute StageService
            log_script.log_info('Starting stage service...')
            arcpy.StageService_server(sddraft_output, sd_output)
            log_script.log_info('Completed stage service.')

            # Execute UploadServiceDefinition
            # Use URL to a federated server
            log_script.log_info('Starting upload SD file to portal...')
            arcpy.UploadServiceDefinition_server(sd_output, server)
            log_script.log_info('Completed upload SD file to portal.')
        else:
            # If the sddraft analysis contained errors, display them
            print(analyzeMessages['errors'])

try:
    log_script.log_info('Initiate publishing tools.')
    publish_GP.create_GP_SD()
    log_script.log_info('Publishing completed successfully.')
except Exception as e:
    raise(e)