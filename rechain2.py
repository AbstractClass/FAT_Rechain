import subprocess


def to_int_list(value, split_char):
    return list(map(int, value.split(split_char)))


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

# Int Conversion
for key in fs_attributes:
    try:
        fs_attributes[key] = int(fs_attributes[key])
    except:
        pass

# Craft dd command for FAT table
bs = str(fs_attributes['Sector Size'])
skip = str(fs_attributes['* FAT 0'][0])
count = str(fs_attributes['* FAT 0'][1] - fs_attributes['* FAT 0'][0])
of = "FAT_Table_0.dd"

cmd = ['dd', 'if='+img_path, 'bs='+bs, 'skip='+skip, 'count='+count, 'of='+of]
dd = subprocess.Popen(args=cmd)

if fs_attributes['File System Type Label'] == 'FAT32':
    rs = 4
elif fs_attributes['File System Type Label'] == 'FAT16':
    rs = 2
else:
    print("FILESYSTEM IS NOT FAT!  PROGRAM WILL NOT RUN CORRECTLY OR IT WILL CRASH!")
    print("read size (rs) is being set to -1 as punishment.")
    rs = -1

fat_table = []
with open('FAT_Table_0.dd', 'rb') as table:
    while True:
        entry = table.read(rs)
        if entry != b'':
            fat_table.append(entry[::-1])
        if not entry:
            break

entry = b'\x00\x00\x00\x00'
while entry == b'\x00\x00\x00\x00':
    fat_table.pop()
    entry = fat_table[-1]

alloc_clusters = []
for cluster, entry in enumerate(fat_table):
    value = "ERROR"
    if entry == b'\x00\x00\x00\x00':
        continue
    elif entry == b'\x0f\xff\xff\xf8' or entry == b'\x0f\xff\xff\xff':
        value = "EOF"
    else:
        value = int.from_bytes(entry, byteorder='big')

    alloc_clusters.append([cluster, value])

cluster_chains = [x for x in alloc_clusters if x[1] == 'EOF']
cluster_pointers = [x for x in alloc_clusters if x[1] != 'EOF']

for pointer in sorted(cluster_pointers, reverse=True):
    for n in range(0, len(cluster_chains)):
        if pointer[1] == cluster_chains[n][0]:
            cluster_chains[n].insert(0, pointer[0])

# Craft dd command for root directory
# skip = str(fs_attributes['*** Root Directory'][0])
# count = str(fs_attributes['*** Root Directory'][1] - fs_attributes['*** Root Directory'][0])

# cmd = ['dd', 'if='+img_path, 'bs='+bs, 'skip='+skip, 'count='+count]

# dd = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
# dd_hex = subprocess.check_output(('hexdump'), stdin=dd.stdout).decode('utf-8')

print(cluster_chains)