#include <iostream>
using namespace std;

int maxim (int x , int y , int z)   // both function prototype and definition.(with no ;).
{
	int greatest;
	x > y ? greatest = x : greatest = y;
	greatest < z ? greatest = z : greatest ;

	return greatest;
}

int main()
{
	int num1 = 10;
	int num2 = 20000;
	int num3 = 54355;
	cout << "Enter 3 numbers : ";	
	cout << "Max is " << maxim (num1 , num2 , num3) << endl;

	return 0;
}
