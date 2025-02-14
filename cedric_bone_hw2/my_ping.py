'''
FUNCTION my_ping():
    1. parse_args()  # parse command-line arguments: -c, -i, -s, -t, and the destination host/IP

    2. resolve destination_host to IP_address (e.g., via DNS)

    3. create a raw ICMP socket (requires admin/root privileges):


    4. initialize statistics counters:

    5. sequence_number = 1

    6. LOOP until (packets_sent == count) OR (timeout reached if specified):
  
    7. after the loop:


    8. close icmp_socket
END FUNCTION

'''