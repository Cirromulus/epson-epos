
run: printStatic
	./printStatic 192.168.0.250

printStatic: printStatic.c
	gcc printStatic.c -o printStatic
