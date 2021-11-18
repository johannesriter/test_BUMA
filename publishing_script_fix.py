import arcpy, json
import os, sys
import sys
import datetime, time
import xml.dom.minidom as DOM

from arcpy import analysis
from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential

workspace = r'C:\Users\test_jojo\Documents\ArcGIS\Projects\PitReserve'

def get_KVvalue(name):
    credential = ClientSecretCredential(tenant_id='ae6627ad-4b20-466d-821c-fd9ee7a25a55', client_id='e0839339-e0ff-48a2-8eb7-6e1f83880708', client_secret='~__V7kS.aphhf2C3JBr8.Spo.93nVi7TlJ')
    client = SecretClient(vault_url='https://omine-dev-akv-001.vault.azure.net/', credential=credential)
    
    try:
        secret_bundle = client.get_secret(name)
        return secret_bundle.value
    except:
        print(sys.exc_info())
        return ''
        
def enable_extensions(sddraft_output, soe): # Function to enable extensions
    # Read the sddraft xml.
    doc = DOM.parse(sddraft_output)

    # Find all elements named TypeName. This is where the server object extension
    # (SOE) names are defined.
    typeNames = doc.getElementsByTagName('TypeName')
    for typeName in typeNames:
        # Get the TypeName we want to enable.
        if typeName.firstChild.data == soe:
            extension = typeName.parentNode
            for extElement in extension.childNodes:
                # Enable Feature Access.
                if extElement.tagName == 'Enabled':
                    extElement.firstChild.data = 'true'

    # Write to sddraft.
    f = open(sddraft_output, 'w')
    doc.writexml(f)
    f.close()

class log_script():
    def log_info(message):
        now_time = datetime.datetime.today()
        time_str = datetime.datetime.strftime(now_time, "%d-%m-%Y %H:%M")
        concate_msg = "{} {}".format(time_str, message)
        arcpy.AddMessage(concate_msg)

class publish_feature():
    def create_web_layerSD():
        # Sign in to Portal
        log_script.log_info('Connect to portal...')
        user = '{}'.format(get_KVvalue('ArcGISEnterprise--username'))
        passw = '{}'.format(get_KVvalue('ArcGISEnterprise--password'))
        
        arcpy.SignInToPortal(arcpy.GetActivePortalURL(), user, passw)
        server = r'https://gisdev.bukitmakmur.com/arcgis/admin'

        # Output file name
        service_name = "test_ref_publish"
        sddraft = service_name + ".sddraft"
        sddraft_output = os.path.join(workspace, sddraft)
        sd = service_name + ".sd"
        sd_output = os.path.join(workspace, sd)

        # Reference map to publish
        aprx = arcpy.mp.ArcGISProject(r'C:\Users\test_jojo\Documents\ArcGIS\Projects\PitReserve\PitReserve.aprx')
        map = aprx.listMaps('Test')[0]
        layer = map.listLayers('ESRIDB.SDE.Pit_Reserve_Bdy_Weekly_Result')[0]
        
        # Create FeatureSharingDraft and set metadata, portal folder, and export data properties
        # server_type = 'HOSTING_SERVER' # for hosted layer
        server_type = 'FEDERATED_SERVER' # for referenced layer
        # analyze_weblayer = map.getWebLayerSharingDraft(server_type, 'FEATURE', service_name, [layer])
        analyze_weblayer = map.getWebLayerSharingDraft(server_type, 'MAP_IMAGE', service_name, [layer])
        analyze_weblayer.federatedServerUrl = server
        analyze_weblayer.portalFolder = 'tes'
        analyze_weblayer.copyDataToServer = False # Need to register db first if set to False
        analyze_weblayer.summary = 'test publish with python.'
        analyze_weblayer.tags = 'test, feature layer'
        analyze_weblayer.allowExporting = True

        # Create SD Draft file
        analyze_weblayer.exportToSDDraft(sddraft_output)
        log_script.log_info('Success to create SD Draft file.')
        
        # Delete previous SD file
        if os.path.exists(sd_output):
            os.remove(sd_output)
        else:
            log_script.log_info("The {} file doesn't exist.".format(sd_output))
            
        # Enable extensions on map sever
        enable_extensions(sddraft_output, "FeatureServer")

        # stage & upload the service if the sddraft analysis didn't contain errors
        # analysis = arcpy.mp.AnalyzeForSD(sddraft_output)
        # if analysis['errors'] == {}:
        # Execute StageService
        log_script.log_info('Starting stage service...')
        arcpy.StageService_server(sddraft_output, sd_output)
        log_script.log_info('Completed stage service.')
        
        # Execute UploadServiceDefinition
        log_script.log_info('Starting upload SD file to portal...')
        # arcpy.UploadServiceDefinition_server(sd_output, server_type)
        arcpy.UploadServiceDefinition_server(sd_output, server)
        log_script.log_info('Completed upload SD file to portal.')
        
        # else:
        #     print(analysis['errors'])

try:
    log_script.log_info('Initiate publishing tools.')
    publish_feature.create_web_layerSD()
    log_script.log_info('Publishing completed successfully.')
except Exception as e:
    raise(e)
