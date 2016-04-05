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

important_info = ("File System Type", "FAT 0", "*** Root Directory", "Sector Size", "Cluster Size")

fsstat_important = set()
for x in fsstat:
    if any(i in x for i in important_info):
        fsstat_important.add(x)

fs_attributes = {n[0].strip(): n[1].strip() for n in list(map(lambda x: x.split(": "), fsstat_important))}

# Convert root directory and FAT table sectors to list of ints
fs_attributes['*** Root Directory'] = list(map(int, fs_attributes['*** Root Directory'].split(" - ")))
fs_attributes['* FAT 0'] = list(map(int, fs_attributes['* FAT 0'].split(" - ")))

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

cmd = ['dd', 'if='+img_path, 'bs='+bs, 'skip='+skip, 'count='+count]

dd = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
dd_hex = subprocess.check_output(('hexdump'), stdin=dd.stdout).decode('utf-8')

# Craft dd command for root directory
skip = str(fs_attributes['*** Root Directory'][0])
count = str(fs_attributes['*** Root Directory'][1] - fs_attributes['*** Root Directory'][0])

cmd = ['dd', 'if='+img_path, 'bs='+bs, 'skip='+skip, 'count='+count]

# dd = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
# dd_hex = subprocess.check_output(('hexdump'), stdin=dd.stdout).decode('utf-8')

print(fs_attributes)
print(dd_hex)