import re
import sys

import matplotlib.pyplot as plt
import numpy as np

print(sys.argv)

filenames = [sys.argv[1], sys.argv[2], sys.argv[3]]

line_pattern = re.compile('(.*),(.*),(.*),(.*)')
name_pattern = re.compile('.*times-(.*)\\.csv')
truth = {1:  [{'min': 0, 'max': 1}, {'min': 248, 'max': 255}],
         62: [{'min': 2, 'max': 62}],
         65: [{'min': 63, 'max': 65}],
         98: [{'min': 66, 'max': 98}],
         103: [{'min': 99, 'max': 103}],
         110: [{'min': 104, 'max': 110}],
         113: [{'min': 111, 'max': 113}],
         118: [{'min': 114, 'max': 118}],
         151: [{'min': 119, 'max': 151}],
         247: [{'min': 152, 'max': 247}]
         }

fig, ax = plt.subplots()

for filename in filenames:
    file = open(filename, 'r')
    trial = name_pattern.match(filename).group(1)

    response_times = []
    lines = 0
    for line in file:
        # lines += 1
        # if lines == 1000:
        #     break
        match = line_pattern.match(line)
        search_key = int(match.group(1))
        node_id_str = match.group(2)
        node_id = int(node_id_str) if node_id_str != 'None' else None
        response_time_str = match.group(4)
        response_time = float(response_time_str) if response_time_str else None

        if node_id:
            for range in truth[node_id]:
                if range['min'] <= search_key <= range['max']:
                    response_times.append(response_time)

    sorted_data = np.sort(response_times)
    y = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.plot(sorted_data, y, marker='.', linestyle='none', label=f'Shutdown interval={trial}')

ax.set_title('Cumulative Distribution Function')
ax.set_xlabel('Response Time')
ax.set_ylabel('Percent of Requests')
plt.legend()
plt.savefig('cdf.png', format='png')
