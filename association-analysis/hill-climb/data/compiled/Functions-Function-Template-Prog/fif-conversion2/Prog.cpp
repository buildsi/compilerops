// Function Template
// Syntax:   template <class UserTypeName>
///			 Type0/UserTypeName FunctionName (Type1/UserTypeName Var1 , ...);
// When the template function name is called in the program, then the compiler substitutes the 
///		TypeName  for a proper type.
// To define more than one type parameter follow this syntax: template <class Type1 , class Type2 , ...>
// Note that it is necessary to place  class  before EACH type.
// Every type parameter in the template definition MUST appear in the function's parameter list
///		at least once.

#include <iostream>
using namespace std;

template < class MyType>
MyType maximum (MyType Var1 , MyType Var2 , MyType Var3);

int main()
{
	int int1 = 10;
	int int2 = 10;
	int int3 = 10;

	cout << "Enter 3 integers : ";
	cout << "The MAX is : " << maximum (int1 , int2 , int3) << endl << endl;

	double d1 = 10;
	double d2 = 100;
	double d3 = 10;
	cout << "Enter 3 doubles : ";
	cout << "The MAX is : " << maximum (d1 , d2 , d3) << endl << endl;

	char char1 = 'a';
	char char2 = 'b';
	char char3 = 'c';
	cout << "Enter 3 characters : ";
	cout << "The MAX is : " << maximum (char1 , char2 , char3) << endl << endl;

	return 0;
}

template < class MyType >
MyType maximum (MyType Var1 , MyType Var2 , MyType Var3)
{
	MyType max = Var1;
	if (max < Var2)
		max = Var2;
	if (max < Var3)
		max = Var3;
	return max;
}
