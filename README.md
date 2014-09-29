Steps to execute the dependencyFinder
1.clone the sandbox
2.clone the repo whose dependency need to be found (exp jiva.um)
3.from command prompt execute:-
python <path of dependencyFinder><path of the py file whose dependency need to be found><path to save the dot file><path to save the excel file>
Exp:-
python <path to the sandbox on local/dependencyFinder.py> <path to the repo(src)/jiva.um/Products/ZeUmservice/ZeUMServiceCtrl.py> <path where u wat to ZeUMServiceCtrlDependency.dot trackDependency.xls

Step to create the image
dot -tpng <path and nameof dot file with extention> -o <path to save the image file with name and extention>
Exp:-
dot -Tpng ZeUMServiceCtrlDependency.dot -o ZeUMServiceCtrlDependency.png

steps to apply filter to excel sheet
open the excel sheet
click on data>filters>select autofilters
click on drop down and select module or methods whose impact need to be found
