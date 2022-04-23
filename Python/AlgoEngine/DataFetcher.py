from pymongo import MongoClient
import numpy as np
from collections import defaultdict, OrderedDict

# Imports for STS / OVH / etc
import sys
sys.path.append('..')
try:
    from .utils import *
    from .settings import * 
    from .sts import getSTSHistogram
    from .ovh import getOVH
    from .similarity import getSTSEmd, getOVHEmd, getTDDistance
except:
    from AlgoEngine.utils import *
    from AlgoEngine.settings import * 
    from AlgoEngine.sts import getSTSHistogram
    from AlgoEngine.ovh import getOVH
    from AlgoEngine.similarity import getSTSEmd, getOVHEmd, getTDDistance
import re

#in order to use this AlgoEngine separately, we build this datafetcher by using MySQLdb instead of Django ORM
#it can also be implemented with Django ORM
def query_for_roi_list(client,study_id):
  db = client['dicomRt']
  collection=db.roi
  return list(collection.find({"Study_ID": study_id}))

def query_for_roi_name(client,refroinos):
  db = client['dicomRt']
  collection = db.roi
  return list(collection.find({"ReferenceROInum":refroinos},{"ROIName": 0}))

def query_oar_id(client,name):
  db = client['dicomRt']
  collection=db.roi
  return list(collection.find({"ROIName": name},{"ReferenceROInum":0}))

def query_for_ovh(client,studyID):
  db = client['dicomRt']
  collection=db.ovh
  return list(collection.find({"Study_ID":studyID}))

def query_ovh_exists(client,studyID, ptv_id, oar_id):
  db = client['dicomRt']
  collection=db.ovh
  return list(collection.find({"PTV_ID": ptv_id,"OAR_ID":oar_id,"Study_ID":studyID}))

def query_insert_ovh(client,bin_value, bin_amount, OverlapArea, ptv_id, oar_id, fk_study_id_id):
  db = client['dicomRt']
  table = 'ovh'
  collection=db[table]
  data_temp = {}
  data = {}
  data_temp['Study_ID']=fk_study_id_id
  data_temp['binValue']=bin_value
  data_temp['binAmount']=bin_amount
  data_temp['OverlapArea']=OverlapArea
  data_temp['PTV_ID']=ptv_id
  data_temp['OAR_ID']=oar_id

  data[table].append(data_temp)
  collection.insert_many(data[table])
  
  print('Collection ',table,' Updated')

def query_delete(client,table,study_id,ptv_id,oar_id):
  db = client['dicomRt']  
  collection=db[table]
  q = collection.delete_many({ "Study_ID": study_id, "PTV_ID": ptv_id, "OAR_ID":oar_id })
  print(q.deleted_count, " documents deleted.")

def query_insert_sts(client,elevation, distance, azimuth, amounts ,ptv_id,oar_id,study_id):
  db = client['dicomRt']
  table = 'sts'
  collection=db[table]
  data_temp = {}
  data = {}
  data_temp['Study_ID']=study_id
  data_temp['Elevation']=elevation
  data_temp['Distance']=distance
  data_temp['Azimuth']=azimuth
  data_temp['Amounts']=amounts
  data_temp['PTV_ID']=ptv_id
  data_temp['OAR_ID']=oar_id

  data[table].append(data_temp)
  collection.insert_many(data[table])
  print('Collection ',table,' Updated')

def query_sts_exists(client,study_id,ptv_id,oar_id):
  db = client['dicomRt']
  table = 'sts'
  collection=db[table]
  return list(collection.find({"PTV_ID": ptv_id,"OAR_ID":oar_id,"Study_ID":study_id})) #need to check

def query_for_contour(client,refROInum, structureSetId):
  db=client['dicomRt']
  collection=db.rtContour
  return list(collection.find({"$and":[{"ContourImageSequence.ReferencedSOPInstanceUID": structureSetId},{"ReferenceROInum":refROInum}]}))


def query_for_sts(client,studyID):
  db=client['dicomRt']
  collection=db.sts
  return collection.find({"Study_ID": studyID})

def query_for_image_plane_info(client,Instance_UID):
  db=client['dicomRt']
  collection=db.ctImages
  return list(collection.find({"SOPInstanceUID": Instance_UID}))


def query_save_similarity(client,DBStudyID, TDSimilarity, OVHDisimilarity, STSDisimilarity, TargetOAR_id, TargetPTV_id,
                fk_study_id_id_query, fk_study_id_id_historical):
  db = client['dicomRt']
  table = 'similarity'
  collection=db[table]
  data_temp = {}
  data = {}
  data_temp['DBStudyID']=DBStudyID
  data_temp['TD_dissimilarity']=TDSimilarity
  data_temp['OVH_dissimilarity']=OVHDisimilarity
  data_temp['STS_dissimilarity']=STSDisimilarity
  data_temp['TargetOAR_id']=TargetOAR_id
  data_temp['TargetPTV_id']=TargetPTV_id
  data_temp['fk_study_id_1_id']=fk_study_id_id_query
  data_temp['fk_study_id_2_id']=fk_study_id_id_historical
  data[table].append(data_temp)
  collection.insert_many(data[table])
  print('Collection ',table,' Updated')

        query_roi_id_from_rtroi = "SELECT id from rt_rois where roi_id_id= %s and fk_study_id_id = %s"
        self.cursor.execute(query_roi_id_from_rtroi, [dicom_roi_id, dicom_roi_id])
def query_roi_id_from_rtroi(client,dicom_roi_id,dicom_roi_id):
    db = client['dicomRt']
    collection = db.roi


class DataFetcher():

    def __init__(self,connect_mongo=True):

        """
        Initializes datafetcher by building PYMONGO connection, and saving the connection client.
        Then, funnctions to load data are prepared using the SSH tunnel.

        Parameters
        ----------
        serverURL : str
            Mongo Server URL
        userName : str
            user name for Mongo Database
        password : str
            Password for corresponding user
        """
        self.userName="bme-528"
        self.password="project4"
        self.serverURL="mongodb+srv://"+self.userName+":"+self.password+"@cluster0.x69n5.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        if connect_mongo:
            self.client=MongoClient(self.serverURL)

        print("Finished Setting up database access")


    #with these two functions, we could use with statement with instance of this class
    #because we use with statement with db connection, we want to inherit this convention
    def __enter__(self):
        return DataFetcher()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("exit the context manager")
        #close the db connection
        if self.connection:
            print("close connection")
            self.connection.close()

        #close the ssh connection
        if self.server:
            print("close the server")
            self.server.stop()

        print("finish the exit process")

    def get_spacing(self, studyID):
        """
        Returns the row spacing and column spacing from the DICOM field `PixelSpacing`, and
        returns the slice thickness from the DICOM filed `SliceThickness` from the SQL
        database.

        Parameters
        ----------
        StudyID : string
            ID in the new dataset. Typically a single number, e.g. `'1'` or `'2'`.

        Returns
        -------
        row_spacing : float
            Row spacing for `StudyID`

        column_spacing : float
            Column spacing for `StudyID`

        slice_thickness : float
            Slice thickness for `StudyID`

        """
        rois = query_for_roi_list(self.client,studyID)
        row_spacing = -1
        column_spacing = -1
        slice_thickness = -1

        roi = rois[0]

        Contours = query_for_contour(self.client,roi['id'], roi['fk_structureset_id_id'])
        
        contour = Contours[0]

        image_info = query_for_image_plane_info(contour['ReferencedSOPInstanceUID'])[0]
        
        spacing_array = np.array(image_info['PixelSpacing'].split(','), dtype=np.float32)

        row_spacing = spacing_array[0]
        column_spacing = spacing_array[1]
        slice_thickness = float(image_info['SliceThickness'])

        return row_spacing, column_spacing, slice_thickness

    def get_pixel_spacing(self, studyID):
        return self.pixel_spacing

    def __get_contours(self, roi):
        roi_id = roi['roi_id_id']
        
        contour_dict = {}
        imagePatientOrientaion = {}
        imagePatientPosition = {}
        pixelSpacing = {}
        block_shape = []
        Contours = query_for_contour(self.client,roi['id'], roi['fk_structureset_id_id'])

        for contour in Contours:
            contour_array = np.array(contour['ContourData'].split(','), dtype=np.float32)
            contour_array = contour_array.reshape(contour_array.shape[0] // 3 , 3)

            contour_dict[contour['ReferencedSOPInstanceUID']] = contour_array
            image_info = query_for_image_plane_info(self.client,contour['ReferencedSOPInstanceUID'])[0]
            imagePatientOrientaion[contour['ReferencedSOPInstanceUID']] = np.array(image_info['ImageOrientationPatient'].split(','), dtype=np.float32)
            
            spacing_array = np.array(image_info['PixelSpacing'].split(','), dtype=np.float32)
            pixelSpacing[contour['ReferencedSOPInstanceUID']] = spacing_array

            if not block_shape:
                block_shape = (image_info['Rows'], image_info['Columns'])

            imagePatientPosition[contour['ReferencedSOPInstanceUID']] = np.array(image_info['ImagePositionPatient'].split(','), dtype=np.float32)

        self.pixel_spacing = pixelSpacing
        return getContours(block_shape, contour_dict, image_orientation=imagePatientOrientaion,
                                    image_position=imagePatientPosition, pixel_spacing=pixelSpacing), imagePatientPosition


    def get_contours_by_id(self, studyID, roi_index):
        rois = query_for_roi_list(self.client,studyID)
        
        contour_dict = {}
        image_position = None
        print("Starting contour")
        for roi in rois:
            roi_id = roi['roi_id_id']
            if roi_id != roi_index:
                continue
            contours, image_position = self.__get_contours(roi)
            contour_dict[roi_id] = contours
        return contour_dict, image_position

    def get_contours(self,studyID):
        '''
        Get contour block for all rois under this studyID
        we need fetch following things to construct
        block_shape
        slice_position_z
        contour_data
        image_orientation
        image_position
        pixel_spacing
        :param studyID:

        Parameters
        ----------
        StudyID : string
            ID in the new dataset. Typically a single number, e.g. `'1'` or `'2'`.

        Returns
        --------
        ptv_dict : List of Dict
        a list of dictionaries, the first dictionary contains ptv and the second contains PTV
            in the dictionary the key is the name of ROI, the value is the contour block.

        oar_dict : list of Dict
            a list of dictionaries, the first dictionary contains ptv and the second contains OAR
            in the dictionary the key is the name of ROI, the value is the contour block.
        '''
        rois = query_for_roi_list(self.client,studyID)
        ptv_dict = {}
        oar_dict = {}

        print("Starting contour")
        for roi in rois:
            roi_id = roi['roi_id_id']
            contour_block, roi_block = self.__get_contours(roi)

            # Checks for PTVs using ROI name -> if it contains PTV we assume it is a PTV
            roi_name = query_for_roi_name(self.client,roi_id)
            roi_interpretation = roi["roi_interpretation"]
            if "PTV" in roi_interpretation or "CTV" in roi_interpretation:
                ptv_dict[roi_name] = (contour_block,roi_block)
            elif "none" in roi_interpretation.lower():
                if "ptv" in roi_name.lower():
                    ptv_dict[roi_name] = (contour_block,roi_block)
                else:
                    oar_dict[roi_name] = (contour_block,roi_block)
            else:
                oar_dict[roi_name] = (contour_block,roi_block)

        print("Done with all")
        return ptv_dict,oar_dict

    def get_SOPIDs(self, StudyID):
        """
        Returns a dict of all the SOPIDs for a given StudyID.

        Parameters
        -----------
        StudyID : String 
            The StudyID to get SOPs for 

        Returns
        -------
        SOPIDs : Ordered Dict
            Ordered by z variable, key is Z var, value is SOP ID.


        """
        SOPIDs = OrderedDict()

        # Fetch from SQL and process here
        

        SOPIDs = OrderedDict(sorted(SOPIDs.items(), key=lambda t : t[0], reverse=True)) # Needed to sort into correct position
        return SOPIDs


    def save_ovh(self,ptv_name,oar_name,ovh_hist,studyID):
        '''
        save ovh every time we have
        :param StudyID:
        :return:if the action is a success or not
        '''
        
        #OAR table roi_dict

        # used because pymysql expects list params, not strings 
        # even for only one string
        if type(ptv_name) is not list:
            ptv_name = [ptv_name]
            
        if type(oar_name) is not list:
            oar_name = [oar_name]
        
        ptv_id = query_oar_id(self.client,ptv_name)
        # self.cursor.execute(query_oar_id, ptv_name)
        # ptv_id = self.cursor.fetchone()["id"]
        oar_id = query_oar_id(self.client,oar_name)
        # self.cursor.execute(query_oar_id, oar_name)
        # oar_id = self.cursor.fetchone()["id"]

        # check if ovh already exists, delete if it does
        rows_count = len(query_ovh_exists(self.client,studyID, ptv_id, oar_id))
        if rows_count > 0:
            # query_delete = "DELETE from ovh where fk_study_id_id = %s and ptv_id = %s and oar_id = %s"
            query_delete(self.client,'ovh',studyID, ptv_id, oar_id)

        binValue = ','.join(str(point) for point in ovh_hist[0])
        binAmount = ','.join(str(point) for point in ovh_hist[1])


        query_insert_ovh(self.client,binValue, binAmount, 20,ptv_id, oar_id, studyID)

    def save_sts(self,ptv_name,oar_name,sts_hist, study_id):
        '''
        definition is the same as save_ovh
        :param sts: has the same data structure like the one in save_ovh
        :param StudyID:
        :return:
        '''

        
        ptv_id = query_oar_id(self.client,ptv_name)
        
        oar_id = query_oar_id(self.client,oar_name)
    
        # check if sts already exists, delete if it does
        rows_count = len(query_sts_exists(study_id, ptv_id, oar_id))
        if rows_count > 0:
            query_delete(self.client,'sts',study_id, ptv_id, oar_id)

        elevation = ",".join(str(point) for point in sts_hist[0])
        azimuth = ",".join(str(point) for point in sts_hist[1])
        distance = ",".join(str(point) for point in sts_hist[2])
        amounts = ",".join(str(point) for point in sts_hist[3])

        query_insert_sts(self.client,elevation, distance, azimuth, amounts ,ptv_id,oar_id,study_id)
    
    def get_ovh(self,studyID):
        '''
        get the ovh of this study, if the study has two ptv or more, make it to be a single ptv-ovh
        :param studyID:
        :return: a dictionary, the key is the name of TargetOAR, the value is the histogram
        '''
        # query_for_ovh = 'SELECT * from ovh WHERE fk_study_id_id = %s'

        data = query_for_ovh(self.client,studyID)
        #return it to be a dictionary, the key is the name of oar , the data is the histogram

        ovhDict = defaultdict()

        for row in data:
            ovhDict[str(row['oar_id']) + " " + str(row['ptv_id'])] = (row['bin_value'],row['bin_amount'])

        return ovhDict

    def get_sts(self,studyID):
        '''

        :param studyID:
        :return: a dictionary, the key is the name of TargetOAR, the value is the histogram
        '''
        query_for_sts = 'SELECT * from sts WHERE fk_study_id_id = %s'

        data = query_for_sts(self.client,studyID)

        stsDict = defaultdict()

        for row in data:
            stsDict[str(row['oar_id']) + " " + str(row['ptv_id'])] = (row['elevation_bins'],row['distance_bins'],
                row['azimuth_bins'],row['amounts'])

        return stsDict

    def save_similarity(self,
            DBStudyID,
            TDSimilarity,
            OVHDisimilarity,
            STSDisimilarity,
            TargetOAR_id,
            TargetPTV_id,
            fk_study_id_id_query,
            fk_study_id_id_historical):

        '''
        save a instance of sim
        :param similarity_paris:
        :param StudyID:
        :return:
        '''
        query_save_similarity(self.client,DBStudyID, TDSimilarity, OVHDisimilarity, STSDisimilarity, TargetOAR_id, TargetPTV_id,
                fk_study_id_id_query, fk_study_id_id_historical)
        
    def get_target_dose(self, study_id, dicom_roi_id):
        """
        Parameters
        ----------

        dicom_roi_id : integer
            corresponds to the DICOM ROI id of a given RTROI
        """

        # Conversion from roi to rt_roi (original in oar_dictionary to rt roi contour)
        query_roi_id_from_rtroi = "SELECT id from rt_rois where roi_id_id= %s and fk_study_id_id = %s"
        self.cursor.execute(query_roi_id_from_rtroi, [dicom_roi_id, study_id])
        roi = self.cursor.fetchone()
        roi_id = roi["id"]
        


        query_target_dose = "SELECT DVHMeanDose from rt_dvh where DVHReferencedROI_id = %s and fk_study_id_id = %s"
        self.cursor.execute(query_target_dose, [roi_id, study_id])

        data = self.cursor.fetchall()
        

        for row in data:
            return float(row["DVHMeanDose"])

    def get_dbstudy_list(self,studyID):
        '''
        Get a list of the names of db study
        :param studyID: is to eliminate the study belongs to the same patient
        :return: a list
        '''
        self.cursor.execute(query_for_study_list,str(studyID))
        study_list = self.cursor.fetchall()
        return list(study_list)

    def fetch_similarity(self,studyID):
        '''
        find similarity of this studyID
        :param studyID:
        :return:dict
        {
            studyID:similarity
        }
        '''
        pass
