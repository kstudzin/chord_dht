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
        response_time = match.group(4)

        if response_time:
            total_responses += 1
        total_requests += 1
        all_total_requests.append(total_requests)
        all_total_responses.append(total_responses/total_requests)

    ax.plot(all_total_requests, all_total_responses, marker='.', linestyle='none', label=f'Shutdown interval={trial}')

ax.set_title('Percent Responses of Total Requests')
ax.set_xlabel('Number of Requests')
ax.set_ylabel('Percent Received Response')
plt.legend()
plt.savefig('percent_responses.png', format='png')
