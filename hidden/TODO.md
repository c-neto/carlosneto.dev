1. Ephemeral Ports
- These are temporary, high-numbered ports (e.g., 49152–65535) used by the client to initiate TCP connections.
- They allow distinguishing multiple simultaneous connections originating from the same IP.
- Example: when opening an SFTP connection (SSH on port 22 of the server), the client uses a local ephemeral port to communicate.

2. How Does the Server “Know” the Client’s Port?
- In the TCP protocol, each packet carries:
- Source IP and port (client)
- Destination IP and port (server)
- The server sees the client’s ephemeral port and responds directly to it, ensuring proper communication.

3. Stateful vs Stateless
- Stateful: the device (firewall, Security Group) tracks the state of connections and automatically allows response traffic.
- Stateless: the device analyzes each packet in isolation and requires explicit rules for both inbound and outbound traffic.

4. Security Group in AWS
- It is a stateful virtual firewall, applied at the instance level.
- It has Inbound (incoming) and Outbound (outgoing) rules:
- Inbound defines who can initiate connections to the instance.
- Outbound defines where the instance can initiate connections to.
- Because it is stateful, the SG automatically allows response traffic, even if there is no explicit rule for the opposite direction.

5. Why Do Security Groups Have Inbound and Outbound Rules if They Are Stateful?
- Because it is necessary to control who can initiate connections to the instance (inbound).
- And to control where the instance can initiate connections to (outbound).
- The SG enables granular control and security, even while automatically allowing return packets.
