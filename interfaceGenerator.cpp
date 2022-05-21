#include <iostream>
#include <fstream>
#include <algorithm>

using namespace std;

bool classFound(ifstream &file, string className){
	string buffer;
	int len = className.size() + 6;
	while(getline(file, buffer)){
		if(buffer.size() > len && buffer.substr(0, len) == "class "+className)
			return true;
	}
	return false;
}

static inline std::string &ltrim(std::string &s) {
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), std::not1(std::ptr_fun<int, int>(std::isspace))));
  return s;
}

void readMethod(ifstream &input, ofstream &output){
	bool docStringStarted = 0;
	string buffer;
	while(getline(input, buffer)){
		ltrim(buffer);
		if(buffer.find("\"\"\"") != string::npos){
			output << "\t\t" << buffer << "\n";
			if(docStringStarted) break;
			else docStringStarted = true;
		}
		else if(docStringStarted) output << "\t\t\t" << buffer << "\n";
		else break;
	}
	output << "\t\tpass\n\n";
}

// A bit dumb but it is still handy and practical. Sadly, considers also inner methods :( 
void generateInterface(ifstream &input, string outPath, string interfaceName, string className){
	ofstream output(outPath);
	output << "class "+interfaceName+"(metaclass=ABCMeta):\n"
						"\t\"\"\"\n"
						"\t\tInterface DocString Here\n"
						"\t\"\"\"\n";

	string buffer;

	while(getline(input, buffer)){
		if(isalpha(buffer[0])){
			break; // End of class reached
		}

		ltrim(buffer);

		// reading public methods declarations neglecting all private methods and special methods (constructors, __call__, etc...)
		if(buffer.size() > 4 &&  buffer.substr(0, 4) == "def " && buffer.substr(4, 2) != "__"){
			output << "\t@abstractmethod\n\t" << buffer << "\n";
			readMethod(input, output);
		}
	}
}

void paramError(){
	cout << "This script searches for python class in a certain file and generates the corresponding interface implementation\n";
	cout << "Right Parameter Format (in any order): -i <input file> -o <output file> -interfaceName <interface name> -className <class name>\n";
	exit(0);
}

int main(int argc, char* argv[]){
	string inPath, outPath, interfaceName, className;

	if (argc < 9) paramError();
	
	for(int i=1; i < argc; i+=2){
		if(argv[i] == string("-i")){
			inPath = argv[i+1];
		}
		else if (argv[i] == string("-o")){
			outPath = argv[i+1];
		}
		else if(argv[i] == string("-interfaceName")){
			interfaceName = argv[i+1];
		}
		else if(argv[i] == string("-className")){
			className = argv[i+1];
		}
		else paramError();
	}

	if (inPath.size() && outPath.size() && interfaceName.size() && className.size()){
		ifstream input(inPath);

		if(input.good() && classFound(input, className))
			generateInterface(input, outPath, interfaceName, className);
		else cout << "File or Class Not Found";
	}
	
	else paramError();	
}