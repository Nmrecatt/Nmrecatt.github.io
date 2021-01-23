import face_recognition.api as face_recognition
import os,shutil
import json
import numpy
from PIL import Image
from datetime import date,datetime
import excel
def match(opath,epath,erpath,departments,year,sub,hour):
	now = datetime.now()
	time=str(now.strftime("%I:%M %p"))
	project=str(os.getcwd()+"/")
	default=str(project+"static/images/")
	originallist={}
	for department in departments:
		jsonpath=str(default+department+"/"+year+"/subjects/"+sub+"/original.json")
		data = open(jsonpath,"r")
		n=data.read()
		temp_list=json.loads(n)
		originallist.update(temp_list)
	for i in originallist:
		originallist[i]=numpy.asarray(originallist[i])
	l=[]
	for a in range(0,2):
		#extracted images encoding
		extractedlist=[]
		for filename in os.listdir(epath):
			sublist=[]
			filename=str(filename)
			sublist.append(filename)
			file_path=epath+filename
			image=face_recognition.load_image_file(file_path)
			image_encoding=face_recognition.face_encodings(image,num_jitters=5)
			if len(image_encoding)>0:
				image_encoding=image_encoding[0]
				sublist.append(image_encoding)
				extractedlist.append(sublist)
			else:
				shutil.move(epath+filename,erpath)
		
		for key in originallist:
			rollno=key[0:10]
			if rollno in l:
				continue 
			for esublist in extractedlist:
				oimg=originallist[key]
				eimg=esublist[1]
				result=face_recognition.compare_faces([oimg],eimg,tolerance=0.4)
				if result[0]== True:
					l.append(rollno)
					os.remove(epath+esublist[0])
					extractedlist.remove(esublist)
					break
	absent=[]
	present=0
	for department in departments:
		xl_fname=department+"_"+year+"_"+sub+".html"
		excelpath=str(default+department+"/"+year+"/subjects/"+sub+"/excel/")
		xlhtmlpath=str(project+"templates/excel_html/"+xl_fname)
		c,a=excel.create_sheet(l,hour,excelpath,xlhtmlpath,time)
		#xl_f1=str(project+"templates/excel_html/"+departments[0]+"_"+year+"_"+sub+".html","")
		absent+=a
		present+=c
	return present,absent


