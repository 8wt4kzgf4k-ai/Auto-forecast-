from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

PORT = 8080

with TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
    print("Serving on port", PORT)
    httpd.serve_forever()
