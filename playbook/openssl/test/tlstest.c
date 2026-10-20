/* Fetch an HTTPS URL through the system libcurl.so.2 (the browser's network stack) and report the TLS result. */
#include <stdio.h>
#include <curl/curl.h>
#include <openssl/opensslv.h>

static size_t sink(void *p, size_t s, size_t n, void *u) { (void)p; (void)u; return s * n; }

int main(int argc, char **argv)
{
    CURL *c;
    CURLcode rc;
    long code = 0, verify = 0;
    if (argc < 2) { fprintf(stderr, "usage: %s URL [CAfile]\n", argv[0]); return 2; }
    printf("libcurl: %s\n", curl_version());
    curl_global_init(CURL_GLOBAL_ALL);
    c = curl_easy_init();
    curl_easy_setopt(c, CURLOPT_URL, argv[1]);
    curl_easy_setopt(c, CURLOPT_WRITEFUNCTION, sink);
    curl_easy_setopt(c, CURLOPT_VERBOSE, 1L);
    curl_easy_setopt(c, CURLOPT_TIMEOUT, 30L);
    if (argc > 2) curl_easy_setopt(c, CURLOPT_CAINFO, argv[2]);
    rc = curl_easy_perform(c);
    curl_easy_getinfo(c, CURLINFO_RESPONSE_CODE, &code);
    curl_easy_getinfo(c, CURLINFO_SSL_VERIFYRESULT, &verify);
    printf("RESULT rc=%d (%s) http=%ld verify=%ld\n", rc, curl_easy_strerror(rc), code, verify);
    curl_easy_cleanup(c);
    return rc;
}
