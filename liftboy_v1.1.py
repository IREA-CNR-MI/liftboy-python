"""
Python software (v3.6+) implementing semantic lift of XML metadata on the basis of appropriate EDI templates
Author: Cristiano Fugazza (fugazza.c@irea.cnr.it)
"""

from SPARQLWrapper import SPARQLWrapper, JSON
from lxml import etree
from copy import deepcopy
from html import unescape, escape
import re
import requests
import json
import sys
#import html
#import urllib.parse

inputFile = None
input = None
templateFile = None
template = None
nsm = None
xmlns = None
logFile = None
# whether the element requires lift
liftNeeded = False
# a dictionary containing, before lift, the value of the item (key) and, after the lift, the URIs that were returned
liftableItems = {}
# string and index for the "_XritX" stuff initialized here
idTail = ""
tailIndex = 0

# inserted for dummy nodes to be post-processed
dummyTail = ""
dummyIndex = 0

elementList = None
documentRoot = None


# escape characters in text
def escape_text(text):
    #escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('/', '&#x2F;').replace('"', '&quot;').replace("'", '&#x27;')
    escaped_text = text.replace('<', '&lt;').replace('>', '&gt;').replace('/', '&#x2F;').replace( '"', '&quot;').replace("'", '&#x27;')
    return escaped_text


# collect the input data
def collect_input(metadata_file,template_file):
    global inputFile
    global input
    global templateFile
    global template
    global nsm
    global xmlns
    global logFile
    inputFile = metadata_file
    # parse the metadata file
    input = etree.parse('input/'+inputFile)
    # get the namespaces in the input file
    root = input.getroot()
    nsm = root.nsmap
    # if the metadata file contains the schema location attribute
    if "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation" in root.attrib:
        # retrieve the first part of the schema location attribute
        schemaLoc = root.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"]
        schemaLoc = schemaLoc[:schemaLoc.find(' ')]
    else:
        # provide a dummy schema location withe no associations
        schemaLoc = "foo"
    if template_file == '':
        # load dictionary containing template associations to schema locations
        templateList = eval(open("app/templateList.py").read())
        # if the file contains an association for schemaLoc
        if schemaLoc in templateList.keys():
            # get the template file name
            templateFile = templateList.get(schemaLoc)
    else:
        # the template file is the second argument in the script call
        templateFile = template_file
    # parse the template file
    template = etree.parse('templates/'+templateFile)
    # one-item list containing the XML namespace
    xmlns = {'xml': 'http://www.w3.org/XML/1998/namespace'}
    # create log file
    logFile = open('log/' + inputFile[:inputFile.rfind('.')] + '.log', 'w')
    logFile.write("start processing file "+inputFile + '\r')

    # debug: show the namespaces associated with the input file
    # print(nsm)


# make input path a full path
def make_path_full(root, path):
    # if path is not a full path
    if path.find(root) == -1:
        if path.startswith('/'):
            thePath = root + path
        else:
            thePath = root + '/' + path
    # else path is a full path
    else:
        thePath = path
    return thePath


# make input path a relative path
def make_path_relative(root, path):
    # if path is not a full path
    if path.find(root) == -1:
        thePath = path
    # else path is a full path
    else:
        thePath = path[path.rfind(root)+len(root):]
    if thePath == "":
        thePath = "."
    else:
        thePath = "." + thePath
    return thePath


# make path simple (i.e., remove node patterns enclosed in square brackets)
def make_path_simple(path):
    outString = path.replace("\r", " ").replace("\n", " ")
    for result in re.findall(r"\[.*?\]", outString):
        outString = outString.replace(result,"")

    # debug:
        #print("removing string " + result + " from " + outString)
    #print("returning string " + outString)

    return outString


# turn a list of paths into a list of full paths and return
# a list of lists containing the individual steps in the paths
def get_path_array(list, root):
    allPaths = []
    for item in list.keys():
        itemContent = list.get(item)
        path = itemContent.get("path")
        thePath = make_path_full(root, path)
        splitPath = thePath.split('/')
        while "" in splitPath:
            splitPath.remove("")

        # debug
        # print("splitPath for item " + item + ": " + str(splitPath))

        if (list[item].get("datatype") == "codelist") or (list[item].get("datatype") == "autoCompletion"):
            global liftNeeded
            liftNeeded = True
            global liftableItems
            liftableItems[item] = {}
        allPaths.append(splitPath)
    return allPaths


# return the list of full paths defined by an item list
def get_plain_paths_array(list, root):
    allPaths = []
    for item in list.keys():
        itemContent = list.get(item)
        path = itemContent.get("path")
        thePath = make_path_full(root, path)
        allPaths.append(thePath)
    return allPaths


# return tha longest sub-path that is contained in all paths in a list
def compute_max_common_path(paths):
    result = ""
    searchEnded = False
    steps = paths[0]
    stepInd = 0
    while not searchEnded:
        lenEquals = True
        for splitPath in paths:
            # if "stepInd" exceeds the length of "steps", then we are done with the loop
            if stepInd >= len(steps):
                searchEnded = True
            # if step does not correspond in ANY of the paths associated with items, "searchEnded" turns to True
            elif splitPath[stepInd] != steps[stepInd]:
                searchEnded = True
            # if lenght of SOME path is lower than the current path, "lenEquals" turns to False
            if len(splitPath) < stepInd + 1:
                lenEquals = False
        if (not searchEnded) and lenEquals:
            result = result + '/' + steps[stepInd]
            stepInd += 1
    return result


# create the XML subtree corresponding to item definition (itemList) on the basis of the input data (node)
def create_items_block(node, itemList, maxCommonPath):
    # create "items" block
    items = etree.Element("items")
    # iterate over the individual items
    for itemKey in itemList.keys():
        # variable "itemDetails" contains the dictionary corresponding to a specific item of the target element
        itemDetails = itemList.get(itemKey)

        # debug:
        #print("creating nodes for item " + itemKey)

        item = etree.SubElement(items, "item")
        theValue = ""
        for detailKey in itemDetails.keys():
            detail = etree.SubElement(item, detailKey)
            if (detailKey != "path" and detailKey != "id" and detailKey != "element_Id") or liftNeeded:
                detail.text = itemDetails.get(detailKey)
            elif detailKey == "id":
                if (itemDetails.get("element_Id") != 'loc_geo') and (itemDetails.get("element_Id") != 'est_temp'):
                    detail.text = itemDetails.get(detailKey)[:itemDetails.get(detailKey).rfind('_')] + idTail + itemDetails.get(detailKey)[itemDetails.get(detailKey).rfind('_'):]
                elif idTail == '':
                    detail.text = itemDetails.get(detailKey)[:itemDetails.get(detailKey).rfind('_')] + idTail + itemDetails.get(detailKey)[itemDetails.get(detailKey).rfind('_'):]
                else:
                    app = itemDetails.get(detailKey)[:itemDetails.get(detailKey).rfind('_')]
                    detail.text = app[:app.rfind('_')] + idTail + app[app.rfind('_'):] + itemDetails.get(detailKey)[itemDetails.get(detailKey).rfind('_'):]
            elif detailKey == "element_Id":
                detail.text = itemDetails.get("element_Id") + idTail
            # in this case, detailKey == "path"
            else:
                # remove node checks from path of items in elements not requiring semantic lift
                detail.text = escape_text( make_path_simple(itemDetails.get("path")) )

        if len(node.xpath(make_path_relative(maxCommonPath, itemDetails.get("path")), namespaces=nsm)) > 0:
            # if the XPath ends with an attribute
            if '@' in itemDetails.get("path")[itemDetails.get("path").rfind('/'):]:
                # if the item has a value different from "" associated with it
                if str(node.xpath(make_path_relative(maxCommonPath, itemDetails.get("path")), namespaces=nsm)[0]) != "":
                    theValue = str(node.xpath(make_path_relative(maxCommonPath, itemDetails.get("path")), namespaces=nsm)[0])
            else:
                # if the item has a value associated with it
                if node.xpath(make_path_relative(maxCommonPath, itemDetails.get("path")) + '/text()', namespaces=nsm):
                    theValue = str(node.xpath(make_path_relative(maxCommonPath, itemDetails.get("path")) + '/text()', namespaces=nsm)[0])

        # try normalize all strings
        #theValue = escape(re.sub(' +', ' ', theValue.replace('\n', ' ')))
        theValue = escape_text(re.sub(' +', ' ', theValue.replace('\n', ' ')))
        theValue = str(theValue.encode('ascii', 'xmlcharrefreplace'))
        theValue = theValue[theValue.find("b\'")+2:-1]

        # debug:
        print("looking for value at index " + str(tailIndex) + " in " + itemDetails.get("path") + " found " + str(theValue))
        logFile.write("looking for value at index " + str(tailIndex) + " in " + itemDetails.get("path") + " found " + str(theValue) + '\r')

        childElem = etree.SubElement(item, "value")
        childElem.text = escape_text(theValue)
        #childElem.text = theValue
        childElem = etree.SubElement(item, "labelValue")
        childElem.text = escape_text( theValue )
        #childElem.text = theValue
        # add item id to the list of items to be lifted
        if itemList.get(itemKey).get("datatype") == "codelist" or itemList.get(itemKey).get("datatype") == "autoCompletion":
            liftableItems[itemKey] = theValue
        # if "useURN" is true, then populate node "languageNeutral"
        if itemList.get(itemKey).get("useURN") == "true":
            childElem = etree.SubElement(item, "urnValue")
            #childElem.text = theValue
            childElem.text = escape_text( theValue )
        # if item has datatype "function", then populate node "query"
        if itemList.get(itemKey).get("datatype") == "function":
            childElem = etree.SubElement(item, "query")
            childElem.text = itemList.get(itemKey).get("hasValue")

        # debug: print content of variable "item"
        # print(etree.tostring(item, pretty_print=True))

    return items


# composes the dictionary for a given template item
def create_item_descr(item, itemId, path, id):
    # variable "id" contains, when not blank, the unique id used for the geographic and temporal extents
    if id != "":
        theId = id
    else:
        theId = itemId
    # variable "element_Id" contains the id of the element corresponding to the item
    element_Id = itemId[:itemId.rfind("_")]
    hasPath = path
    hasDatatype = item.attrib["hasDatatype"]
    isFixed = item.attrib["isFixed"]
    if "useCode" in item.attrib:
        useCode = item.attrib["useCode"]
    else:
        useCode = ""
    if "useURN" in item.attrib:
        useURN = item.attrib["useURN"]
    else:
        useURN = ""
    if "outIndex" in item.attrib:
        outIndex = item.attrib["outIndex"]
    else:
        outIndex = ""
    languageNeutral = ""

    # DOVE PRENDERE QUESTO VALORE? E' SIGNIFICATIVO? PARE NON LO SIA
    listeningFor = ""

    if "isLanguageNeutral" in item.attrib:
        isLanguageNeutral = item.attrib["isLanguageNeutral"]
    else:
        isLanguageNeutral = ""
    if "datasource" in item.attrib:
        datasource = item.attrib["datasource"]
    else:
        datasource = ""
    hasIndex = item.attrib["hasIndex"]
    if "field" in item.attrib:
        field = item.attrib["field"]
    else:
        field = ""
    itmId = ""
    if "show" in item.attrib:
        show = item.attrib["show"]
    else:
        show = ""
    if item.xpath("descendant::defaultValue/text()"):
        defaultValue = item.xpath("descendant::defaultValue/text()")[0]
    else:
        defaultValue = ""
    if item.xpath("descendant::hasValue/text()"):
        hasValue = item.xpath("descendant::hasValue/text()")[0]
    else:
        hasValue = ""
    # create the dictionary decsribing the item
    listItem = {"id": theId, "element_Id": element_Id, "path": hasPath, "datatype": hasDatatype, "fixed": isFixed,
                "useCode": useCode,
                "useURN": useURN, "outIndex": outIndex, "languageNeutral": languageNeutral,
                "listeningFor": listeningFor, "isLanguageNeutral": isLanguageNeutral,
                "datasource": datasource, "hasIndex": hasIndex, "field": field, "itemId": itmId, "show": show,
                "defaultValue": defaultValue, "hasValue": hasValue}
    return listItem


# execute semantic lift on a node sub-tree (nodes) corresponding to of a specific item (item) of a specific
# element (element)
def do_semantic_lift(nodes, element, items):
    endpoint = ""
    query = ""
    outputTree = etree.Element("outputTree")

    # debug:
    print("BEGIN semantic lift for items " + str(items) + " of element " + element)
    logFile.write("BEGIN semantic lift for items " + str(items) + " of element " + element + '\r')

    uriDict = {}
    for item in items.keys():
        uriList = []
        type = template.xpath("//element[@xml:id='" + element + "']/descendant::item[@xml:id='" + item + "']/@hasDatatype", namespaces=xmlns)[0]
        datasource = template.xpath("//element[@xml:id='" + element + "']/descendant::item[@xml:id='" + item + "']/@datasource", namespaces=xmlns)[0]
        # if the item to be lifted is of type "codelist"
        if type == "codelist":
            thesaurus = template.xpath("//codelist[@xml:id='" + datasource + "']/uri/text()", namespaces=xmlns)[0]
            endpoint = template.xpath("//sparqlEndpoint/text()", namespaces=xmlns)[0]
            #query = template.xpath("//codelistQuery/text()", namespaces=xmlns)[0].replace("$thesaurus_name", thesaurus).replace("$search_param", items.get(item))
            query = template.xpath("//codelistQuery/text()", namespaces=xmlns)[0].replace("$thesaurus_name", thesaurus).replace("$search_param", re.sub(' +', ' ',items.get(item).replace('\n',' ')))
        # else the item to be lifted is of type "autoCompletion"
        elif type == "autoCompletion":
            if len( template.xpath("//sparql[xml:id='" + datasource + "']/url/text()", namespaces=xmlns) ) > 0:
                endpoint = template.xpath("//sparql[xml:id='" + datasource + "']/url/text()", namespaces=xmlns)[0]
            else:
                endpoint = template.xpath("//sparqlEndpoint/text()", namespaces=xmlns)[0]
            #query = template.xpath("//sparql[@xml:id='" + datasource + "']/query/text()", namespaces=xmlns)[0].replace("$search_param", items.get(item))
            query = template.xpath("//sparql[@xml:id='" + datasource + "']/query/text()", namespaces=xmlns)[0].replace("$search_param", re.sub(' +', ' ',items.get(item).replace('\n',' ')))

        # debug
        #print("the endpoint is " + endpoint)
        #print("the query is " + query)

        if endpoint != "":
            sparql = SPARQLWrapper(endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                uriList.append(result["c"]["value"])
            uriDict[item] = uriList

    # debug: insert fake URIs
    #if len(uriDict.keys()) > 1:
    #    for elem in uriDict:
    #        uriDict.get(elem).append("http://foo.bar")
    print("END   semantic lift for items " + str(uriDict) + " of element " + element)
    logFile.write("END   semantic lift for items " + str(uriDict) + " of element " + element + '\r')

    isEmpty = True
    for key in uriDict.keys():
        if uriDict.get(key) != []:
            isEmpty = False

    if isEmpty == False:
        create_lifted_nodes(nodes, uriDict)
    else:
        #pass
        create_dummy_nodes(nodes, uriDict)


# update nodes with results from lift
def create_lifted_nodes(nodes, items):
    global idTail
    global tailIndex

    # debug: output call parameters
    print("call to function create_lifted_nodes for items " + str(items))
    logFile.write("call to function create_lifted_nodes for items " + str(items) + '\r')

    # the variable indicating whether to execute recursion
    execRecursion = False
    targetItem = ""
    outputTree = etree.Element("outputTree")
    # check whether recursion is required
    for item in items:
        if len(items.get(item)) > 1:
            execRecursion = True
            targetItem = item
            break
    if execRecursion:
        # call the function for each URI for targetItem
        for uri in items.get(targetItem):
            # create the shortened dictionary
            targetDict = {}
            for item in items:
                if item == targetItem:
                    targetDict[item] = [uri]
                else:
                    targetDict[item] = items.get(item)
            # execute recursion
            create_lifted_nodes(nodes, targetDict)
    else:
        # create copy of nodes
        copyOfNodes = deepcopy(nodes)
        # add the _XritX stuff
        newId = item[:item.rfind('_')] + idTail
        idNode = copyOfNodes.xpath("./id")[0]
        idNode.text = newId
        # for each item being lifted, create the <codeValue> tag
        for item in items:
            # if lift was successful
            if len(items.get(item)) > 0:
                # find the item being lifted
                targetNode = copyOfNodes.xpath("descendant::item[id = '" + item + "']")[0]
                # create "codeValue" element
                subtag = etree.SubElement(targetNode, "codeValue")
                #subtag.text = items.get(item)[0]
                subtag.text = escape_text( items.get(item)[0] )
        # for each item defined in the element
        for nodeId in copyOfNodes.xpath("descendant::item/id"):
            # add the _XritX stuff
            newId = nodeId.text[:nodeId.text.rfind('_')] + idTail + nodeId.text[nodeId.text.rfind('_'):]
            nodeId.text = newId
            #datatypeNode = nodeId.xpath("../datatype")[0]
            #if datatypeNode.text == "select":
                #datatypeNode.xpath("../value")[0].text = ""
                #datatypeNode.xpath("../labelValue")[0].text = ""
        for pathNode in copyOfNodes.xpath("descendant::path"):
            # insert simple path for items in elements requirting lift
            #pathNode.text = make_path_simple(pathNode.text)
            pathNode.text = escape_text( make_path_simple(pathNode.text) )
        idTail = idTail + "_XritX"
        tailIndex += 1
        documentRoot.append(copyOfNodes)


# update nodes with results to be passed down to the stylesheet
def create_dummy_nodes(nodes,items):
    global dummyTail
    global dummyIndex

    # debug: output call parameters
    print("call to function create_lifted_nodes for items " + str(items))
    logFile.write("call to function create_dummy_nodes" + '\r')

    dummyRoot = etree.Element("dummyNode")

    # the variable indicating whether to execute recursion
    # SHOULD ALWAYS BE False IN THIS FUNCTION
    execRecursion = False
    targetItem = ""
    outputTree = etree.Element("outputTree")
    # check whether recursion is required
    for item in items:
        if len(items.get(item)) > 1:
            execRecursion = True
            targetItem = item
            break
    if execRecursion:
        # THIS BRANCH SHOULD NEVER BE THE CASE
        pass
    else:
        # create copy of nodes
        copyOfNodes = deepcopy(nodes)
        # add the dummy _XritX stuff
        newId = item[:item.rfind('_')] + dummyTail
        idNode = copyOfNodes.xpath("./id")[0]
        idNode.text = newId
        # for each item being lifted, create the <codeValue> tag
        # THERE SHOULD BE NONE
        '''
        for item in items:
            # if lift was successful
            if len(items.get(item)) > 0:
                # find the item being lifted
                targetNode = copyOfNodes.xpath("descendant::item[id = '" + item + "']")[0]
                # create "codeValue" element
                subtag = etree.SubElement(targetNode, "codeValue")
                #subtag.text = items.get(item)[0]
                subtag.text = escape_text( items.get(item)[0] )
        '''
        # for each item defined in the element
        for nodeId in copyOfNodes.xpath("descendant::item/id"):
            # add the dummy _XritX stuff
            newId = nodeId.text[:nodeId.text.rfind('_')] + dummyTail + nodeId.text[nodeId.text.rfind('_'):]
            nodeId.text = newId
            #datatypeNode = nodeId.xpath("../datatype")[0]
            #if datatypeNode.text == "select":
                # POSSIBLY THESE ARE THE LINES TO BE CHANGED TO PRESERVE DATA IN NODES NOT LIFTED
                #datatypeNode.xpath("../value")[0].text = ""
                #datatypeNode.xpath("../labelValue")[0].text = ""
        for pathNode in copyOfNodes.xpath("descendant::path"):
            # insert simple path for items in elements requirting lift
            #pathNode.text = make_path_simple(pathNode.text)
            pathNode.text = escape_text( make_path_simple(pathNode.text) )
        dummyTail = dummyTail + "_XritX"
        dummyIndex += 1
        dummyRoot.append(copyOfNodes)
        documentRoot.append(dummyRoot)


# composes the dictionary containing the elements in the template
def create_target_list():
    # extract the elements in the template
    elementsOfInterest = template.xpath("//element")
    # variable "outList" will contain the output dictionary
    outList = {}
    # for each element in the template
    for elt in elementsOfInterest:
        id = elt.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        isMandatory = elt.attrib["isMandatory"]
        hasRoot = elt.xpath("./hasRoot/text()")[0]
        itemList = {}
        # for each item defined by the element
        for itm in elt.xpath("descendant::item"):
            itemId = itm.attrib["{http://www.w3.org/XML/1998/namespace}id"]
            paths = itm.xpath("descendant::hasPath/text()")
            prefix = itm.xpath("@xml:id", namespaces=xmlns)[0]
            #app = itm.xpath("@xml:id", namespaces=xmlns)[0]
            #prefix = app[:app.rfind('_')]
            #suffix = app[app.rfind('_'):]
            # if the item is a standard one
            if len(paths) == 1:
                listItem = create_item_descr(itm, itemId, make_path_full(hasRoot,  paths[0]), "")
                itemList[itemId] = listItem
            # if the item is a bounding box
            elif itm.attrib["hasDatatype"] == "boundingBox":
                #loc_geo_itemIds = ["loc_geo_westLongitude", "loc_geo_eastLongitude", "loc_geo_northLatitude", "loc_geo_southLatitude"]
                loc_geo_itemIds = [prefix + "_westLongitude", prefix + "_eastLongitude", prefix + "_northLatitude", prefix + "_southLatitude"]
                for ind in range(0,4):
                    listItem = create_item_descr(itm, itemId, make_path_full(hasRoot, paths[ind]), loc_geo_itemIds[ind])
                    itemList[itemId + '_' + str(ind)] = listItem
            # if the item is a time range
            elif itm.attrib["hasDatatype"] == "dateRange":
                #est_temp_itemIds = ["est_temp_start", "est_temp_end"]
                est_temp_itemIds = [prefix + "_start", prefix + "_end"]
                for ind in range(0, 2):
                    listItem = create_item_descr(itm, itemId, make_path_full(hasRoot, paths[ind]), est_temp_itemIds[ind])
                    itemList[itemId + '_' + str(ind)] = listItem
        # create the dictionary corresponding to the target element
        listElem = {"id": id, "root": hasRoot, "mandatory": isMandatory, "produces": itemList}
        outList[id] = listElem
    return outList


# create the output file
def create_output_tree():
    root = etree.Element("elements")
    elem = etree.SubElement(root, "version")
    elem.text = templateFile[templateFile.rfind("_v")+2:templateFile.rfind(".xml")]
    elem = etree.SubElement(root, "template")
    elem.text = templateFile[templateFile.rfind("/") + 1:templateFile.rfind("_liftboy")] + '_edi'

    # copy elements in tag "edimlPreamble"
    for e in template.xpath("//edimlPreamble/*", namespaces=xmlns):
        root.append(e)

    elem = etree.SubElement(root, "baseDocument")
    elem.text = template.xpath("//baseDocument", namespaces=xmlns)[0].text

    # populate tags <fileId> and <fileUri> issuing a REST request to the EDI server defined in the template
    # get URL of EDI server from the template
    requestUrl = template.xpath("//metadataEndpoint/text()", namespaces=xmlns)[0]
    # remove trailing slash if needed
    if requestUrl.endswith('/'):
        requestUrl = requestUrl[:-1]
    # complete URL for the REST request
    requestUrl = requestUrl + "/rest/ediml/requestId"
    # execute the request
    #restResponse = requests.get(requestUrl, verify=True)
    restResponse = requests.get(requestUrl, verify=False)
    if (restResponse.ok):
        # Loading the response data into a dict variable
        jData = json.loads(restResponse.content)
        elem = etree.SubElement(root, "fileId")
        elem.text = str(jData["id"])
        elem = etree.SubElement(root, "fileUri")
        #elem.text = str(jData["uri"])
        elem.text = escape_text( str(jData["uri"]) )
    else:
        # If response code is not ok (200), print the resulting http error code with description
        restResponse.raise_for_status()

    return root


# look for the template elements in the input file
def parse_input_file():

    # debug
    #print("__ call to parse_input_file __")

    # for each element in the template
    for elt in elementList.keys():
        global idTail
        global tailIndex
        global dummyTail
        global dummyIndex
        idTail = ""
        tailIndex = 0

        # reset dummy variables
        dummyTail = ""
        dummyIndex = 0

        global liftNeeded
        global liftableItems

        liftNeeded = False
        liftableItems = {}
        elementContent = elementList.get(elt)
        itemList = elementContent.get("produces")
        root = elementContent.get("root")

        # debug
        print("looking in the input file for element " + elt + " with root " + root)
        #print("element " + elt + ": " + str(elementContent))
        logFile.write('\r' + "looking in the input file for element " + elt + " with root " + root + '\r')

        # create an array with all the paths defined by the element
        allPaths = get_path_array(itemList, root)
        # find the sub-path that is contained in all the paths defined by the element
        maxCommonPath = compute_max_common_path(allPaths)

        # debug:
        #print("processed item list for element " + elt + ": maxCommonPath is " + maxCommonPath)

        # maxCommonPath now contains the path to be searched for in the input to single out all instances of the element
        # start searching the input document for the element in hand
        print("start processing the input document for element " + elt + ": " + str(elementContent))
        logFile.write("start processing the input document for element " + elt + ": " + str(elementContent) + '\r')

        # get the list of all (full) paths defined by the element
        plain_paths = get_plain_paths_array(itemList, root)
        # variable containing the list of results, initialized with the results corresponding to first list item
        matchList = input.xpath(plain_paths[0], namespaces=nsm)
        # variable containing the path that returns the least number of results
        targetPath = None
        # compute which path returns the least number of results
        for path in plain_paths:
            newList = input.xpath(path, namespaces=nsm)
            targetPath = plain_paths[0]
            if len(newList) < len(matchList):
                matchList = newList
                targetPath = path
        # compute tha differing part between targetPath and maxCommonPath
        remainingPath = targetPath[targetPath.find(maxCommonPath)+len(maxCommonPath):]
        if len(remainingPath) > 0:
            remainingPath = "." + remainingPath
            targetPattern = maxCommonPath + '[' + remainingPath + ']'
        else:
            targetPattern = maxCommonPath

        # debug
        #print("computed targetPath    = " + targetPath)
        #print("computed maxCommonPath = " + maxCommonPath)
        #print("computed remainingPath = " + remainingPath)
        #print("computed targetPattern = " + targetPattern)

        nodeList = input.xpath(targetPattern, namespaces=nsm)

        # debug: print number of element instances found
        print("found " + str(len(nodeList)) + " instances")
        logFile.write("found " + str(len(nodeList)) + " instances" + '\r')

        if len(nodeList) > 0:
            for node in nodeList:
                # create "element" node
                elem = etree.Element("element")
                # create child nodes
                for elementKey in elementContent.keys():
                    if elementKey != "produces":
                        childElem = etree.SubElement(elem, elementKey)
                        #childElem.text = elementContent.get(elementKey)
                        childElem.text = escape_text( elementContent.get(elementKey) )

                # UNDERSTAND THE ROLE OF ELEMENT "label"
                childElem = etree.SubElement(elem, "label")

                # "represents_element" is the original id
                childElem = etree.SubElement(elem, "represents_element")
                childElem.text = elementContent.get("id")
                itemsBlock = create_items_block(node, itemList, maxCommonPath)
                elem.append(itemsBlock)

                # debug
                #print("Liftneeded: " + str(liftNeeded))

                # if the element contains items of type "codelist" or "autocompletion"
                if liftNeeded:

                    # debug
                    print("lifting element for items " + str(liftableItems))
                    logFile.write("lifting element for items " + str(liftableItems) + '\r')

                    do_semantic_lift(elem, elt, liftableItems)
                else:
                    # add the _XritX stuff
                    idNode = elem.xpath("descendant::id")[0]
                    newId = elementContent.get("id") + idTail
                    idNode.text = newId
                    documentRoot.append(elem)
                    idTail = idTail + "_XritX"
                    tailIndex += 1

                # debug: print content of variable "elem"
                print(etree.tostring(elem, pretty_print=True))
                logFile.write(str(etree.tostring(elem, pretty_print=True)) + "\r")

        # debug
        #print("")

def do_lift(metadata_file, template_file):
    global elementList
    global documentRoot

    collect_input(metadata_file, template_file)
    elementList = create_target_list()

    # debug: elements in the template
    #for elt in elementList.keys():
    #    logFile.write(elt + ": " + str(elementList[elt]) + '\r')

    documentRoot = create_output_tree()
    parse_input_file()
    outputTree = etree.ElementTree(documentRoot)
    outputTree.write("output/" + inputFile[:inputFile.rfind(".")] + ".ediml")
    stylesheets = template.xpath("//xsltChain/xslt/text()", namespaces=xmlns)
    inputTree = outputTree
    for stylesheet in stylesheets:
        xslt = etree.parse(stylesheet)
        transform = etree.XSLT(xslt)
        inputTree = transform(inputTree)
    inputTree.write("output/" + inputFile[:inputFile.rfind(".")] + "_transformed.ediml")

    # post metadata to EDI server
    # get URL of EDI server from the template
    requestUrl = template.xpath("//metadataEndpoint/text()", namespaces=xmlns)[0]
    # remove trailing slash if needed
    if requestUrl.endswith('/'):
        requestUrl = requestUrl[:-1]
    # complete URL for the REST request
    requestUrl = requestUrl + "/rest/metadata"
    headers = {'Content-Type': 'application/xml'}
    #r = requests.post(requestUrl, data=etree.tostring(inputTree, pretty_print=True), headers=headers)
    #logFile.write("metadata post response code: " + str(r.status_code))

    try:
        #r = requests.post(requestUrl, data=urllib.parse.quote_plus(etree.tostring(inputTree, pretty_print=False)), headers=headers, verify=False)
        r = requests.post(requestUrl, data=etree.tostring(inputTree, pretty_print=False), headers=headers, verify=False)
        logFile.write("metadata post response code: " + str(r.status_code))
    except requests.exceptions.RequestException as e:
        logFile.write("metadata post response code: " + str(r.status_code))
        logFile.write("exceptions: " + e)

    logFile.close()
    return outputTree.xpath("//fileId/text()", namespaces=xmlns)

# call do_lift() to run debug
inputFile = sys.argv[1]
if len(sys.argv) > 2:
    templateFile = sys.argv[2]
else:
    templateFile = ''
do_lift(inputFile,templateFile)