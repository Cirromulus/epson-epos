#include <stdio.h>
#include <netdb.h>
#include <stdlib.h>
#include <string.h>

#define Width (80)	// ??

int main(int argc, char* argv[])
{
	int sock;
	struct sockaddr_in addr;
	if (argc != 2) {
		printf("usage: ltcp <ip address>\n");
		exit(1);
	}
	/* create socket */
	sock = socket(AF_INET, SOCK_STREAM, 0);
	if (sock < 0) {
		perror("socket()");
		exit(1);
	}
	/* initialize the parameter */
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_port = htons(9100);
	addr.sin_addr.s_addr = inet_addr(argv[1]);
	/* connect */
	if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
		perror("connect()");
	}
	printf("connected\n");
	/* send data */

    char buf[Width];
    while (fgets(buf, sizeof(buf), stdin)) {
        //printf("%s\n", buf);
        send(sock, buf, strnlen(buf, sizeof(buf)), 0);
    }
    
    char cutPaper[] = {'\n', '\n', 27, '@', 29, 'V', 48};
    send(sock, cutPaper, sizeof(cutPaper), 0);
    
	/* close socket */
	close(sock);
	return 0;
}
