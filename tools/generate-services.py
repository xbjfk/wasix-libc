import sys

class Ports:
    def __init__(self, port: tuple[str, str]):
        self.entries = []
        self.add(port)

    def add(self, port: tuple[str, str]):
        self.entries.append(port)

class Services:
    _instance = None

    ports = dict()

    def __new__(cls, _):
        if cls._instance is None:
            cls._instance = super(Services, cls).__new__(cls)
        return cls._instance

    def __init__(self, filename):
        self.__load(filename)

    def __load(self, filename):
        for line in open(filename):
            if line[0:1] == '#' or line.isspace():
                continue
            line = line[:-1] # drop newline
            self.add(line)

    def add(self, line: str):
        (name, rest) = line.split(None)
        (port, proto) = rest.split('/')
        if name in self.ports:
            self.ports[name].add((port, proto))
        else:
            self.ports[name] = Ports((port, proto))

    def num_ports(self):
        return len(self.ports)


    def generate(self, filename, max_entries=1000):
        with open(filename, 'w') as f:
            len_entries = max_entries
            if len(self.ports) < max_entries:
                len_entries = len(self.ports)

            f.write("#include <uthash.h>\n\n")
            f.write("#include \"lookup.h\"\n")
            f.write("#include \"services.h\"\n\n")
            f.write("services_entry_t *services = NULL;\n")
            f.write(f"static services_entry_t static_services_entries[{len_entries}];\n\n")
            f.write("void add_entry(int idx, char *name, struct service *svc) {\n")
            f.write("\tstatic_services_entries[idx].name = name;\n")
            f.write("\tstatic_services_entries[idx].svcs = svc;\n")
            f.write("\tHASH_ADD_STR(services, name, &static_services_entries[idx]);\n")
            f.write("}\n\n")
            f.write("void init_services() {\n")
            f.write("\tif (services != NULL) {\n")
            f.write("\t\treturn;\n")
            f.write("\t}\n")
            for (i, name) in enumerate(iter(self.ports)):
                if i >= max_entries:
                    break
                ports = self.ports[name]
                f.write(f"\tadd_entry({i}, \"{name}\", (struct service[]){{\n")
                for (j, tpl) in enumerate(iter(ports.entries)):
                    (port, proto) = tpl
                    socktype = ""
                    if proto == "tcp":
                        socktype = "SOCK_STREAM"
                        proto = "IPPROTO_TCP"
                    elif proto == "udp":
                        socktype = "SOCK_DGRAM"
                        proto = "IPPROTO_UDP"
                    else:
                        continue # unsupported sock/proto
            
                    f.write(f"\t\t(struct service){{{port}, {proto}, {socktype}}},\n")
                f.write("\t});\n")
            f.write("}\n")


if __name__ == "__main__":
    max_entries = 1000
    if len(sys.argv) > 1:
        max_entries = sys.argv[1]
    print(max_entries)
    ss = Services("/etc/services")
    ss.generate("services.c", int(max_entries))

