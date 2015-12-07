import socket
import json

def tryWardenLogin(username, password):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('zealot.sirenfal.com', 5000))
	sslSocket = socket.ssl(s)
	sslSocket.write('%s\r\n' % (json.dumps({
		'action': 'auth',
		'pass': 'sDCIJSDcjOASCijasd',
	})))
	sslSocket.write('%s\r\n' % (json.dumps({
		'action': 'checkuser',
		'username': username,
		'password': password,
	})))
	count = 0
	while count < 10:
		resp = json.loads(sslSocket.read(1024))
		print resp
		if resp['action'] == 'checkuser' and resp['response'] == 1:
			s.close()
			return True
		if resp['action'] == 'checkuser':
			break
		count += 1

	s.close()
	return False