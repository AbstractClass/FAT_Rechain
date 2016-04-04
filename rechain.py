import subprocess


def to_cluster(starting_sector, sector, sector_size=512, cluster_size=4096):
    cluster = ((sector - starting_sector) / (cluster_size / sector_size)) + 2
    try:
        return int(cluster)
    except TypeError:
        return "Incorrect Arguments, calculated a float, should be int"


img_path = "/home/connor/Documents/SPR401/FAT-fs.dd"
cmd =["fsstat", img_path]

# Proper method
# call = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# out, err = call.communicate()

# Kinda hacky
call = subprocess.check_output(cmd)

fsstat = call.decode('utf-8').splitlines()

important_info = ["File System Type", "FAT 0", "*** Root Directory", "Sector Size", "Cluster Size", "(8)", "(16)"]

# Search for all relevant info
fsstat_important = set()
for x in fsstat:
    for i in important_info:
        if i in x:
            fsstat_important.add(x)

# Generate a dictionary of title and value for the relevant info
fs_list_split = list(map(lambda x: x.split(": ") if ":" in x else x.split("->"), fsstat_important))

fs_dict = {}
for x in fs_list_split:
    print(x)
    fs_dict[x[0]] = x[1]

# Needed for the to_cluster function
root_sector = int(fs_dict["*** Root Directory"].split(" - ")[0])

# Get all the allocated sectors from fsstat and translate from sectors to cluster

allocated_clusters = {}
for x in fs_dict:
    if '(8)' in x:
        allocated_clusters[to_cluster(root_sector, int(x.split("-")[0]))] = fs_dict[x].strip()
    elif '(16)' in x:
        middle_sector = int(x.split("-")[0]) + 8
        middle_cluster = to_cluster(root_sector, middle_sector)
        allocated_clusters[to_cluster(root_sector, int(x.split("-")[0]))] = middle_sector
        allocated_clusters[middle_cluster] = fs_dict[x].strip()

print("ALLOC_CLUSTERS", allocated_clusters)

# Grab all the pointers and translate from sectors to cluster
# This is a list because I will need to sort it in a minute
allocated_clusters_pointers = [ [x, to_cluster(
                                        root_sector,
                                        int(allocated_clusters[x])
                                    )]
                               for x in allocated_clusters
                               if allocated_clusters[x] != "EOF"]

print("ALLOC_POINTERS", allocated_clusters_pointers)
# We are going to start at the end of each chain and work backwards
cluster_chains = [[x, "EOF"] for x in allocated_clusters if allocated_clusters[x] == "EOF"]

for i in sorted(allocated_clusters_pointers, reverse=True):
    for n in range(0, len(cluster_chains)):
        if i[1] in cluster_chains[n]:
            cluster_chains[n].insert(0, i[0])
print(cluster_chains)