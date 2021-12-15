import re
import sys

import matplotlib.pyplot as plt

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

    total_requests = 0
    total_responses = 0
    all_total_requests = []
    all_total_responses = []
    for line in file:
        match = line_pattern.match(line)
        search_key = int(match.group(1))
        node_id_str = match.group(2)
        node_id = int(node_id_str) if node_id_str != 'None' else None
        response_time_str = match.group(4)
        response_time = float(response_time_str) if response_time_str else None

        if node_id:
            for range in truth[node_id]:
                if range['min'] <= search_key <= range['max']:
                    total_responses += 1
        total_requests += 1
        all_total_requests.append(total_requests)
        all_total_responses.append(total_responses/total_requests)

    ax.plot(all_total_requests, all_total_responses, marker='.', linestyle='none', label=f'Shutdown interval={trial}')

ax.set_title('Percent Correct Responses of Total Requests')
ax.set_xlabel('Number of Requests')
ax.set_ylabel('Percent Correct Received Response')
plt.legend()
plt.savefig('percent_correct_responses.png', format='png')
