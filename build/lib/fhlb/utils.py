def mapt(f,*args):
	return tuple(map(f,*args))

def partition_all(n,data):
	return [data[i:i+n] for i in range(0,len(data),n)]

def partition(n,data):
	return [data[i:i+n] for i in range(0,len(data),n) if len(data[i:i+n]) == n]
