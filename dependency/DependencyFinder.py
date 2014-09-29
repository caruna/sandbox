'''
The Api /tool to find the dependency of the python code (controller/model) in jiva.
Here we are capturing the calls and imports and putting into dictionaries and using 
it to create an dot file and another one to create the excel sheet
'''
import sys
from os.path import isfile
import re
import xlwt,xlrd
from xlutils.copy import copy
from xlutils.styles import Styles
class DependencyFinder():
    def __init__(self):
        ifile=sys.argv[1]
        graphfile=sys.argv[2]
	exfile=sys.argv[3]
        self.readPyFile(ifile,graphfile,exfile)
    
    def AssignColor(self,key='',colors=''):
	''' method to return the color for that perticular module this is while creating the excel sheet'''
	if key and colors:
	    for modname,colorname in colors.iteritems(): # assign colour to the cells other than coloumn header
		if re.search(modname,key):
		    return('font: name Times New Roman, height 230, bold on; borders: top medium, bottom medium, right medium; alignment: horiz centre; pattern: pattern solid, fore_colour '+colorname+';')
	else: # assign colour to the coloumn header
	    return('font: name Times New Roman, height 230, bold on, colour red; borders: top medium, bottom medium, right medium; alignment: horiz centre; pattern: pattern solid, fore_colour white;')
	
    
        
    def AddToWorkbook(self,workbook,funDict,nrow='',colors={}):
	'''this function will append the date to workbook'''
	rincrmt=nrow+1
	keys=funDict.keys()
	worksheet=workbook.get_sheet(0)
	for key,value in funDict.iteritems():
	    keysplit=key.split('_',1)
	    for val in value:
		cincrmt=0
	    	for v in keysplit:
		    worksheet.col(cincrmt).width=256 * 45
		    worksheet.write(rincrmt,cincrmt,v,xlwt.easyxf(self.AssignColor(keysplit[0],colors)))
		    cincrmt+=1
		for v in val:
		    worksheet.col(cincrmt).width=256 * 45
		    worksheet.write(rincrmt,cincrmt,v,xlwt.easyxf(self.AssignColor(val[0],colors)))
		    cincrmt+=1
	    	rincrmt+=1
	return workbook
	
    def appendSubgraph(self,value,restpartofmodule=''):
        ''' return the subgraph string'''
        string=''
        for itrval in value:
            if itrval=='Controller' or itrval=='Model'or itrval=='zsqls':
                itrval=value[0]+"_"+itrval
            if itrval is not value[-2] and itrval is not value[-1] and itrval is not "permissions":
                string+=itrval+"->"
            elif itrval is not value[-1]:
                string+=itrval
        string+=";\n"
        return string
    
    def insertImportDependency(self,modlist,importlist,q):
        '''
        This method will create an list for import 
        modules and inserts into the dictionay and returns dictionary
        '''
        apndlist=[]
        apndlist.extend(importlist)
        apndlist.append(q)
        modlist=self.AddToDictionay(modlist,apndlist)
        return modlist
    
    def splitAndCreateList(self,modlist,importlist,value):
        '''split the line accordingly and create a list '''
        
        valuelist=[]
        funlist=[]
        if re.search('import',value):
            valuelist = value.split(' import ')
            for element in valuelist:
                if re.search('[\(|\,]',element): 		#for import list which uses brackets to import more than one function
                    elementlist=[]
                    elementlist=element.split(',')		# if they are superated by , ie "from product.abcd import (pqrs,efg)"
                    for ele in elementlist:
                        ele=re.sub(r'\W+','',ele)		# it will check for
                        funlist.append(ele)
                    for value in funlist:
                        modlist=self.insertImportDependency(modlist,importlist,value)
                    importlist[:]=[]
                elif not re.search('\*',element): #ignore * element in the import
                    if re.search('from|import',element) and len(element)>4:	#some call contain the string has 'from' part of it whic caused error
                        strwithfrom=element.split(' ')
                        if not re.search('import',element):
                            importlist.append(strwithfrom[1])
                    else:
                        importlist.append(element)
        elif not re.search('Products', value) and not re.search('from', value): #if the value don't cntain from or import or product it will simply add to the list exp: ['from Products', 'ZeUtil', 'security_decorator import log_security_audit_info\n']-> in this list it will work for 'ZeUtil'
            if re.search(' as ', value):
                parse= value.split(' as ')
                importlist.append(parse[0])
            else:
                importlist.append(value)
        return importlist
    
    def AddToDictionay(self,append_dict,apndlist,called_function_name=''):
        ''' it will add the list may be import dependency or call dependency into the dictionary and returns dictionary'''
	call_apndlist=[]
	flg=0
	try:
	    if called_function_name =='':
		key=append_dict.keys()[-1]+1
		append_dict[key]=apndlist
	    elif called_function_name !='':
		key=called_function_name.replace(" ","")
		for k,v in append_dict.iteritems():
		    if k==key:
			value=append_dict[k]
			call_apndlist.extend(value)
			if apndlist in v:
			    flg=1
		if not flg:
		    call_apndlist.append(apndlist)
		append_dict[key]=call_apndlist
	except IndexError:
		append_dict[0]=apndlist
	return append_dict
	
	    
    
    def checkAndInsertIntoDict(self,append_dict,apndlist,called_function_name=''):
        ''' called when the method is called other than import this is check if the method called is for its own controller of model method '''
        flag=0
        try:
            if apndlist[-1]=='Controller' or apndlist[-1]=='Model':
                flag=1
        except IndexError:
            flag=0
        for key,value in append_dict.iteritems():  			# remove dupilcate entry and the call is not itself in the mod list
            if(apndlist==value):
                flag=1
        if apndlist and not flag:
            append_dict=self.AddToDictionay(append_dict,apndlist,called_function_name)
	elif apndlist and called_function_name:
	    append_dict=self.AddToDictionay(append_dict,apndlist,called_function_nam)
        return append_dict
    
    def InsertCallDependency(self,modlist,value,apndlist):
        ''' create and return the list by parsing depending on the condition '''
        if (not (re.search('self',value) or re.search('\(self,',value))): # if the call has self or self as parameter it will ignore the call line
            if not re.search('=',value) :
                apndlist.append(value.replace(" ",""))
            elif re.search('=',value):# and re.search('HL_Integration',value):	#if the call returns the value then parse it with = and get the method name
                valuesplit=value.split('=')
                valuesplit[1]=valuesplit[1].replace(" ","")
                apndlist.append(valuesplit[1])
        return apndlist
            
        
    def readPyFile(self,inputFile,dependencyDotFile,excelfile):
        restpartofmodule=''
        if re.search('Ctrl',inputFile):
            size = inputFile.index('Ctrl') if re.search('Ctrl',inputFile) else len(inputFile)
        elif re.search('Mdl',inputFile):
            size = inputFile.index('Mdl') if re.search('Mdl',inputFile) else len(inputFile)
        if re.search('(AppealEpisodeUMService)',inputFile):
            cmpltModuleName=inputFile[0:size]
            siz = inputFile.index('U') if re.search('U',inputFile) else len(inputFile)
            module=inputFile[0:siz]
            restpartofmodule=inputFile[siz:len(cmpltModuleName)]
        else:
            module=inputFile[2:size]
            siz = inputFile.index('.') if re.search('.',inputFile) else len(inputFile)
            cmpltModuleName=inputFile[2:siz]
        linesplit=[]
        modulename=[]							#stores module names
        modlist={}							#stores the dictionary of dependencies
        colours={}							#stores colours for the module
        numbofcountformodule={}						#count for number of times module been called from an file
	called_function_name=''
	funDict={}
        linepre=""							#for multiple lines 	
        with open(inputFile) as fp:
            flg=1
            for line in fp:						# for each line in the file
                if linepre and re.search('\)',line):    		# for multiple lines involved in the call join all the lines and then perform rest of the operation
                    linepre+=line
                    line=linepre
		if re.search('(def\s)',line):
		    start=line.index('f')+1
		    called_function_name=cmpltModuleName+'_'+line[start:line.index('(')]
                if re.search('[\']{3}|[\"]{3}',line):			#if the line read is an documentaion line we are setting the flag=0 in the begning and closing document flag=1
                    tstflg=re.findall('[\']{3}|[\"]{3}',line)
                    if flg==1 and len(tstflg)<2:			#if tstflg>2 ie the ''' is closing in same line		
                        flg=0
                    else:
                        flg=1
                    #check to filter the lines in the file
                elif flg and (re.search('self',line) and not re.search('((?<='+module+')\.)|(Ze'+module+'\s)',line)) and not re.search('\.\_',line) and (not re.search('\)\.',line) or re.search('self.[\w.]+\w',line)) and not re.search('%s',line)and not re.search('\w[\.|\_]views',line) and not re.search('def[^\_]',line) and not re.search('cms.',line) and not re.search('self.(Model|Controller|logo)',line) and (not re.search('(((?<=self.)(REQUEST|request))|((?<=(request.)|(REQUEST.))(set|get)))',line) or re.search('(((?<=_request)\W)|((?<=\(self.)(REQUEST|request)))',line)) and not re.search('dtml|common_slot',line) and not re.search('self[.|%]\w+\(',line) and not re.search('#',line) and not re.search('acl_users',line) or (re.search('Products',line) and not re.search('#',line)  and not re.search('(Ze'+module+'\s)',line)) or re.search('permissions',line): #(\s\.\w) this patten will search all the lines are like "from .permissions import permissions" but was stuck up with "from permissions import permissions" thats why changed to re.search('permissions',line)
                    linesplit=line.split('.')			
                    listval=[]                    
                    if re.search('from|import\s',line) and not re.search('_from|\sfrom|from_',line) and not re.search('Ctrl',line):   # this is used to list all import modules
                        if re.search('\(',line) and re.search('[\,[\\]\n]',line) and not re.search('\)',line):			#line in import which is accross more than one line join those lines	{add for my refernce :'\)' added for sentinel 			
                            line=line.rstrip('\t\n\r')
                            linepre=line
                        else:									#when the line is in properly joined and valid perfrom other operation
                            importlist=[]
                            try :
                                for element in linesplit:
                                    element=element.strip()
                                    importlist=self.splitAndCreateList(modlist,importlist,element)		#split and create list
                            except:
                                importlist=self.splitAndCreateList(modlist,importlist,linesplit)
                            if importlist:
                                modlist= self.AddToDictionay(modlist,importlist)			# add to dictionary
                            linepre=""
                    elif not re.search('import',line) or re.search('_from|^from',line): # not re.search('import|from',line) changed for diagnosis						#for methods called other than imported		
                        MoreThanOneModule=re.findall('self.[\w.]+\w',line)  				# Creates an list of module calls if the line have more than one in an line exp: I_START_REC_NO = (I_CUR_PAGE * self.ZeUI.getDefRecPerPage()) - self.ZeUI.getDefRecPerPage()
                        if len(MoreThanOneModule)>1:
                            # check if all those calls are same ,if not then check for each call
                            if MoreThanOneModule[0]!=MoreThanOneModule[1]:				
                                for dependent in MoreThanOneModule:		
                                    apndlist=[]
                                    if not re.search('self.[zsql|REQUEST]',dependent):
                                        splitdependent=dependent.split('.')
                                        for element in splitdependent:
                                            apndlist=self.InsertCallDependency(modlist,element,apndlist)
                                    modlist=self.checkAndInsertIntoDict(modlist,apndlist)
				    funDict=self.checkAndInsertIntoDict(funDict,apndlist,called_function_name)
                            #more than one call in a line and they are same
                            elif not re.search('self.zsql',MoreThanOneModule[0]):
                                splitdependent=MoreThanOneModule[0].split('.')
                                apndlist=[]
                                for element in splitdependent:
                                    apndlist=self.InsertCallDependency(modlist,element,apndlist)
                                modlist=self.checkAndInsertIntoDict(modlist,apndlist)
				funDict=self.checkAndInsertIntoDict(funDict,apndlist,called_function_name)
                        else:
			    flgifmoduleisimported=0
                            try:    # this is invoked when the method call is only one in an given line exp:self.Episode.Controller.getDSForEpisodeView(main_list)
                                call=MoreThanOneModule[0]
				test=''
				test=re.search('self.[A-z]+\_',line)
                                if not re.search('self.id',call) and not re.search('self.zsql',call) and not re.findall('self.[\w.]+\[',line) and not re.search('(?i)self.'+module+'\_',call) and not re.search('self.[A-z]+\_',call):
                                    calllist=call.split('.')
                                    if calllist[1]!=restpartofmodule: # and not re.search(calllist[3],call): this is not working for diagnosis
                                        for element in calllist:
                                            element=element.replace(" ","")
                                            listval=self.InsertCallDependency(modlist,element,listval)
                            except:#this is invoked when the module is imported and it doesn't uses self.
				#for element in linesplit:
				    #print 'element',element
				    #linesplit[linesplit.index(element)]=element.replace(" ","")
				#print 'linesplit123',linesplit
				for key,val in modlist.iteritems():
				    for element in linesplit:
					element=element.replace(" ","")
					if element in val:
					    flgifmoduleisimported=1
				if flgifmoduleisimported:				# if the modules are imported from product or present in the import list then only its functions are extracted
				    for element in linesplit:                                   
                                    	siz = element.index('(') if re.search('\(',element) else len(element)
                                    	element=element[0:siz]
                                    	element=element.replace(" ","")
                                    	listval=self.InsertCallDependency(modlist,element,listval)
                            modlist=self.checkAndInsertIntoDict(modlist,listval)
			    funDict=self.checkAndInsertIntoDict(funDict,listval,called_function_name)
        fp.close()
	''' this section is to create the worksheet'''
	colors={'permissions':'red','Episode':'light_green','Procedure':'turquoise','Provider':'orange','ZeUtil':'pink','ZeSentinel':'green','Sentinel':'green','ZeUI':'teal_ega','ZeUser':'yellow','ZeCache':'periwinkle','Patient':'Gold','Lookup':'Lavender','ProviderPortal':'dark_blue_ega','WorkList':'light_blue','PREpisode':'cyan_ega','Diagnosis':'dark_red_ega','Document':'ocean_blue','Notes':'sky_blue','UMService':'rose','Widget':'light_orange','Assessment':'Plum','UDF':'magenta_ega','Keyword':'light_yellow','zelogger':'olive_green','kriya':'purple_ega','Guidelines':'white','ZeJiva':'pale_blue','Extensions':'blue','Notification':'lime','WorkFlow':'DarkViolet','Reports':'Coral','IPEpisode':'aqua','OPEpisode':'sea_green','faxes':'dark_blue','Fax':'dark_blue','ActivityWorkFlow':'olive_ega','EducationalMaterial':'gray_ega','Email':'Tan','OutReachScript':'ivory','Payour':'silver_ega','Payor':'dark_yellow','LCNEpisode':'teal','CMEpisode':'light_turquoise','Contact':'bright_green','SQLWrapper':'dark_green_ega','ContextPermission':'gray25'}
	if isfile(excelfile):
	    wrkbok = xlrd.open_workbook(excelfile,formatting_info=True)
	    ws=wrkbok.sheet_by_name('Back_track_dependency')
	    rows=ws.nrows-1
	    wrkbok=copy(wrkbok)
	else:
	    wrkbok=xlwt.Workbook()
	    ws=wrkbok.add_sheet('Back_track_dependency')
	    ws=wrkbok.add_worksheet('Back_track_dependency')
	    ws.write(0,0,'Calling Module',xlwt.easyxf(self.AssignColor()))
	    ws.write(0,1,'Calling Method',xlwt.easyxf(self.AssignColor()))
	    ws.write(0,2,'Called Module',xlwt.easyxf(self.AssignColor()))
	    ws.write(0,3,'Called Method',xlwt.easyxf(self.AssignColor()))
	    ws.write(0,4,'Called Method',xlwt.easyxf(self.AssignColor()))
	    ws.write(0,5,'Called Method',xlwt.easyxf(self.AssignColor()))
	    rows=0
	wrkbok=self.AddToWorkbook(wrkbok,funDict,rows,colors)
	wrkbok.save(excelfile)
	
	''' section to create graph and sub graph'''	
	procedurename=[]
        colours={'permissions':'red','Episode':'YellowGreen','Procedure':'turquoise','Provider':'orange','ZeUtil':'pink','ZeSentinel':'green','Sentinel':'green','ZeUI':'gray','ZeUser':'yellow','ZeCache':'PaleGoldenRod','Patient':'Gold','Lookup':'Lavender','ProviderPortal':'AntiqueWhite','WorkList':'AliceBlue','PREpisode':'Cyan','Diagnosis':'DarkOrchid','Document':'BlueViolet','Notes':'SkyBlue','UMService':'Thistle','Widget':'PaleVioletRed','Assessment':'Plum','UDF':'Magenta','Keyword':'OldLace','zelogger':'DarkSeaGreen','kriya':'HotPink','Guidelines':'DarkSalmon','ZeJiva':'CornflowerBlue','Extensions':'Blue','Notification':'Orchid','WorkFlow':'DarkViolet','Reports':'LightCoral','IPEpisode':'MediumAquaMarine','OPEpisode':'LightSeaGreen','faxes':'LightSteelBlue','Fax':'LightSteelBlue','ActivityWorkFlow':'RosyBrown','EducationalMaterial':'SlateGray','Email':'Tan','OutReachScript':'DarkKhaki','Payour':'Azure','Payor':'Azure','LCNEpisode':'WhiteSmoke','CMEpisode':'DarkOrange','Contact':'Crimson','SQLWrapper':'Chocolate','ContextPermission':'DodgerBlue'}
        string="strict digraph DependencyGraphfor"+cmpltModuleName+"\n{ \n rankdir=LR; \n node[shape=box,style=filled];\nZe"+cmpltModuleName+"[shape=box3d,fillcolor=Magenta];"
        for key,value in modlist.iteritems(): # this is to create the module list without duplication
            try:
                if value[0] not in modulename:
                    if value[0]!='Ze'+module:
                        modulename.append(value[0])
            except IndexError:
                print 'error occured in module name at key=',key,' and value =',value
            try: #create procedure list without duplication as we need to avoid the conflict between procedure name and module name
                if value[1] not in procedurename:
                    procedurename.append(value[1])
            except IndexError:
                print 'error occured in procedure name at key=',key,' and value =',value
        for key in modulename:		# remove the modulename which are listed in procedurename
            for k in procedurename:
                if key == k and (key != 'permissions' and key != 'zelogger' and key != 'ZeUtil'):
                    modulename.remove(key)
        modlist=sorted(modlist.values())	# we are sorting the dictionary inorder to create the dot file after sorting it will be stored as a list
        for vl in modlist:
            for v in modlist:
                try :
                    if v[0]==vl[1] and v[0]!='ZeUtil' and v[0]!='permissions' and v[0]!='zelogger': #checking that previouse module name is same as the current as we need to group them with same module name
                        for i in v:
                            if i!=v[0]: # list with same string 2 times example permission.permission
                                vl.append(i)
                except IndexError:
                    print "to avoid two line entry if the imported functioned function have same name"  
        previousmodule="none"
        callcount=0
        for value in modlist:                    #appending 0  or 1 to modlist as we need to add ze<module name> if 0 else body of subgraph
            for val in modulename:
                if val==value[0]:
                    if previousmodule == value[0]:
                        callcount+=1
                        value.append('1')
                    else:
                        callcount=1                              #it will include starting value + rest of the values
                        value.append('0')
                numbofcountformodule[value[0]]=callcount
            previousmodule=value[0]
        conterformodule=0
	#print 'test123',funDict
        col="red"
        for value in modlist:		
            for k in modulename:
                if k == value[0] and value[-1]=='0':
                    conterformodule=1
                    for ky,val in colours.iteritems():
                        if ky == k:
                            col=colours[ky]
                    string+="\nsubgraph "+value[0]+"{\n node[fillcolor="+col+"];\n"+value[0]+"[shape=egg];\n Ze"+cmpltModuleName+"->"
                    string+=self.appendSubgraph(value)
                elif k == value[0] and value[-1]=='1':
                    conterformodule+=1
                    string+=self.appendSubgraph(value)
            if(value[0] in modulename and numbofcountformodule[value[0]]==conterformodule):
                string+="}\n"
        string+='}'
        fp=open(dependencyDotFile, "wb")
        fp.write(string)
        fp.close()  
obj=DependencyFinder()
#(not re.search('(((?<=self.)(REQUEST|request))|((?<=(request.)|(REQUEST.))(set|get)))',line) or re.search('(((?<=_request)\W)|((?<=\(self.)(REQUEST|request)))',line)) .... needed to modify because "decoded_request = self.ZeUtil.Model.menuUrlDecode(self.REQUEST.QUERY_STRING)" in diagnosis controller
