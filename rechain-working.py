import subprocess


def to_int_list(value, split_char):
    return list(map(int, value.split(split_char)))

def craft_cmd(sector_size, coords, of):
    bs= str(sector_size)
    skip = str(coords[0])
    count = str(coords[1] - coords[0])

    return ['dd', 'if='+img_path, 'bs='+bs, 'skip='+skip, 'count='+count, 'of='+of]

def read_byte_entries(of, rs):
    fat_table = []
    with open(of, 'rb') as table:
        while True:
            entry = table.read(rs)
            if entry != b'':
                fat_table.append(entry[::-1])
            if not entry:
                break

    return fat_table

def remove_trailing_zeroes(table):
    entry = b'\x00\x00\x00\x00'
    while entry == b'\x00\x00\x00\x00':
        table.pop()
        entry = table[-1]

    return table

def get_alloc_clusters(table):
    alloc_clusters = []
    for cluster, entry in enumerate(table):
        if entry == b'\x00\x00\x00\x00':
            continue
        elif entry == b'\x0f\xff\xff\xf8' or entry == b'\x0f\xff\xff\xff':
            value = "EOF"
        else:
            value = int.from_bytes(entry, byteorder='big')

        alloc_clusters.append([cluster, value])

    return alloc_clusters

def chain_it(cmd, of, rs):
    dd = subprocess.Popen(args=cmd)
    dd.communicate()

    fat_table = read_byte_entries(of, rs)

    fat_table = remove_trailing_zeroes(fat_table)

    alloc_clusters = get_alloc_clusters(fat_table)

    cluster_chains = [x for x in alloc_clusters if x[1] == 'EOF']
    cluster_pointers = [x for x in alloc_clusters if x[1] != 'EOF']

    for pointer in sorted(cluster_pointers, reverse=True):
        for n in range(0, len(cluster_chains)):
            if pointer[1] == cluster_chains[n][0]:
                cluster_chains[n].insert(0, pointer[0])

    return cluster_chains


img_path = "/home/connor/Documents/SPR401/FAT-fs.dd"


cmd =["fsstat", img_path]
###################################################################################
# Proper method
# call = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# out, err = call.communicate()
###################################################################################

# Kinda hacky
call = subprocess.check_output(cmd)

fsstat = call.decode('utf-8').splitlines()

important_info = ("File System Type", "FAT 0", "FAT 1","*** Root Directory", "Sector Size", "Cluster Size")

fsstat_important = set()
for x in fsstat:
    if any(i in x for i in important_info):
        fsstat_important.add(x)

fs_attributes = {n[0].strip(): n[1].strip() for n in list(map(lambda x: x.split(": "), fsstat_important))}

# Convert root directory and FAT table sectors to list of ints
fs_attributes['*** Root Directory'] = to_int_list(fs_attributes['*** Root Directory'], ' - ')
fs_attributes['* FAT 0'] = to_int_list(fs_attributes['* FAT 0'], ' - ')
fs_attributes['* FAT 1'] = to_int_list(fs_attributes['* FAT 1'], ' - ')

# Lazy int Conversion
for key in fs_attributes:
    try:
        fs_attributes[key] = int(fs_attributes[key])
    except:
        pass

# Determine read size (in bytes)
if fs_attributes['File System Type Label'] == 'FAT32':
    rs = 4
elif fs_attributes['File System Type Label'] == 'FAT16':
    rs = 2
else:
    print("FILESYSTEM IS NOT FAT!  PROGRAM WILL NOT RUN CORRECTLY OR IT WILL CRASH!")
    print("read size (rs) is being set to -1 as punishment.")
    rs = -1

# Get fat 0 chain
fat_0_of = 'FAT_Table_0.dd'
fat_0_cmd = craft_cmd(fs_attributes['Sector Size'], fs_attributes['* FAT 0'], fat_0_of)
fat_0_chain = chain_it(fat_0_cmd, fat_0_of, rs)

# Get fat 1 chain
fat_1_of = 'FAT_Table_1.dd'
fat_1_cmd = craft_cmd(fs_attributes['Sector Size'], fs_attributes['* FAT 1'], fat_1_of)
fat_1_chain = chain_it(fat_1_cmd, fat_1_of, rs)

fls = subprocess.check_output(('fls', img_path)).decode('utf-8')

fls_clusters = set()
for n in range(0, len(fls)):
    if fls[n] == ':':
        num = ''
        i = n - 1
        while True:
            if fls[i].isdigit():
                num += fls[i]
                i -= 1
            else:
                fls_clusters.add(int(num[::-1]))
                break

parented_clusters = []
for chain in fat_0_chain:
    for cluster in fls_clusters:
        if cluster in chain:
            parented_clusters.append(chain)

orphan_clusters = [x for x in fat_0_chain if x not in parented_clusters]

print("FAT CHAIN: ", fat_0_chain)
print("FLS CLUSTERS: ", fls_clusters)
print("PARENTED CLUSTERS: ", parented_clusters)
print("ORPHANS: ", orphan_clusters)