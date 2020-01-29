/** termctl.c
 * Send messages to the Terminale server socket. */

#include <stdlib.h>   /* exit, strtoul */
#include <stdio.h>    /* stdout, stderr, fprintf, fputs */
#include <string.h>   /* strlen, strcpy */
#include <stdbool.h>  /* bool, true, false */
#include <errno.h>    /* errno, ENXIO */
#include <getopt.h>   /* getopt_long, optarg, optind,
                       * struct option, no_argument, required_argument */
#include <sys/socket.h>  /* socket, connect, setsockopt,
                            send, recv, shutdown,
                            struct sockaddr,
                            AF_UNIX, SOCK_STREAM,
                            SOL_SOCKET, SO_SNDTIMEO, SO_RCVTIMEO,
                            SHUT_RDWR */
#include <sys/un.h>  /* struct sockaddr_un */

static char const*const version = "1.0";

static void usage(FILE * outfile, char const* name) {
    fprintf(outfile,
"usage: %s [OPTIONS] [MESSAGE]\n"
"\n"
"Send MESSAGE to the Terminale server socket, where MESSAGE is one of:\n"
"  toggle             toggle window visibility (default)\n"
"  quit               shut down the server\n"
"\n"
"optional arguments:\n"
"  -h, --help         show this message and exit\n"
"  -v, --version      show version number and exit\n"
"  -s, --socket=PATH  send messages to PATH\n"
"                     (default \"/etc/terminale/.server.skt\")\n"
"  -t, --timeout=MS   set socket timeout to MS milliseconds\n"
"                     (default 100)\n"
"\n",
            name);
}

/* getopt options */
static const struct option long_opts[] = {
    {"help"   , no_argument      , NULL, 'h'},
    {"version", no_argument      , NULL, 'v'},
    {"socket" , required_argument, NULL, 's'},
    {"timeout", required_argument, NULL, 't'},
    {0, 0, 0, 0}  /* NULL terminator */
};
static char const*const short_opts = "hvst";

struct sockaddr_un skaddr = {
    .sun_family = AF_UNIX,
    .sun_path = "/etc/terminale/.server.skt",
};
#define UNIX_PATH_MAX 108

struct timeval timeout = {
    .tv_sec = 0,
    .tv_usec = 100000,
};

static inline int parse_options(int argc, char ** argv) {
    int opt;
    while ((opt = getopt_long(argc, argv, short_opts, long_opts, NULL)) != -1)
        switch (opt) {
        case 'h':
            usage(stdout, argv[0]);
            exit(0);
        case 'v':
            puts(version);
            exit(0);
        case 's':
            if (strlen(optarg) >= UNIX_PATH_MAX) {
                fprintf(stderr, "socket path '%s' too long (max length %d)\n",
                        optarg, UNIX_PATH_MAX - 1);
                return 1;
            }
            strcpy(skaddr.sun_path, optarg);
            continue;
        case 't': {
            char *endptr;
            unsigned long ms = strtoul(optarg, &endptr, 10); 
            if (ms == 0 || endptr[0] != '\0') {
                fprintf(stderr, "invalid timeout '%s'"
                                " (must be positive decimal integer)\n",
                        optarg);
                return 1;
            }
            timeout.tv_sec = ms / 1000;
            timeout.tv_usec = (ms % 1000) * 1000;
            continue;
            }
        default:
            usage(stderr, argv[0]);
            return 1;
        }
    /* optind is now the start index of the remaining (non-flag) arguments */
    return 0;
}

#define MESSAGES_COUNT 2
static char const*const valid_messages[MESSAGES_COUNT] = {"toggle", "quit"};
static char const message_bytes[MESSAGES_COUNT] = {'t', 'q'};
static char const ack_message = 'a';

static inline bool is_prefix(char const* prefix, char const* word) {
    for (int i = 0; prefix[i] != '\0'; i++)
        if (word[i] != prefix[i])
            return false;
    return true;
}

static inline int message_index(char const* message) {
    for (int i = 0; i < MESSAGES_COUNT; i++)
        if (is_prefix(message, valid_messages[i]))
            return i;
    return -1;
}

int main(int argc, char ** argv) {
    if (parse_options(argc, argv) != 0)
        return 1;
    if (argc - optind > 1) {
        usage(stderr, argv[0]);
        return 1;
    }
    int msg_idx = argc - optind == 0 ? 0 : message_index(argv[optind]);
    if (msg_idx == -1) {
        fprintf(stderr, "invalid message: '%s'\n", argv[optind]);
        return 1;
    }

    int sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sockfd == -1) {
        fprintf(stderr,
                "error creating new streaming unix-domain socket [%d]\n",
                errno);
        return 1;
    }
    int r = 0;
    if (connect(sockfd, (struct sockaddr *)(&skaddr), sizeof(skaddr)) != 0) {
        fprintf(stderr, "error connecting to socket '%s' [%d]\n",
                skaddr.sun_path, errno);
        r = 1;
        goto _cleanup;
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout))
            != 0) {
        fprintf(stderr, "error setting send-timeout for socket '%s' [%d]\n",
                skaddr.sun_path, errno);
        r = 1;
        goto _cleanup;
    }
    if (send(sockfd, &(message_bytes[msg_idx]), 1, 0) != 1) {
        fprintf(stderr, "error sending '%c' to socket '%s' [%d]\n",
                message_bytes[msg_idx], skaddr.sun_path, errno);
        r = 1;
        goto _cleanup;
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout))
            != 0) {
        fprintf(stderr, "error setting recv-timeout for socket '%s' [%d]\n",
                skaddr.sun_path, errno);
        r = 1;
        goto _cleanup;
    }
    char ack;
    if (recv(sockfd, &ack, 1, 0) != 1) {
        fprintf(stderr, "error receiving ack from socket '%s' [%d]\n",
                skaddr.sun_path, errno);
        r = 1;
        goto _cleanup;
    }
    if (ack != ack_message) {
        fprintf(stderr, "received unexpected ack: '%c'\n", ack);
        r = 1;
    }
_cleanup:
    if (shutdown(sockfd, SHUT_RDWR) != 0) {
        fprintf(stderr, "error shutting down socket '%s' [%d]\n",
                skaddr.sun_path, errno);
        r = 1;
    }
    return r;
}
