from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8

def checksum(data_bytes):
    csum = 0
    countTo = (len(data_bytes) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = data_bytes[count + 1] * 256 + data_bytes[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(data_bytes):
        csum = csum + data_bytes[len(data_bytes) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = time.time() - startedSelect
        if whatReady[0] == []:
            return "The request that you made is timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        ICMPHeader = recPacket[20:28]
        pack_type, code, checksum, pack_id, seq = struct.unpack("bbHHh", ICMPHeader)
        timeSent, = struct.unpack("d", recPacket[28:])

        rtt = (timeReceived - timeSent) * 1000
        ip_header = struct.unpack('!BBHHHBBH4s4s', recPacket[:20])
        sender = inet_ntoa(ip_header[8])

        timeLeft = timeLeft - howLongInSelect

        return f"Reply from {sender} time={rtt}"

def sendOnePing(mySocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)  
    myChecksum = htons(myChecksum & 0xFFFF)  
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay

def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    while True:
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)

    return delay

#ping("31.13.66.35")
#ping("google.com")
#ping("208.67.222.222")
ping("82.129.253.33")
