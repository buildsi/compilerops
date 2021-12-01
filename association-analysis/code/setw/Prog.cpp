#include <iostream>
#include <math.h>
#include <iomanip>
using namespace std;

int main()
{
	int BaseNo = 10;
	int ExpoNo = 20;
	cout << setw(16) << setiosflags(ios::fixed) << pow(BaseNo,ExpoNo) << endl;

	return 0;
}
