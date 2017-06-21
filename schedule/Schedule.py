import os
import sys
import yaml

FILEPATH = os.path.expanduser('~') + '/cs105/FirstCourse/.schedule.yml'

class Schedule(object):
    tasks = None

    def __init__(self):
        if os.path.isfile(FILEPATH):
            with open(FILEPATH, 'r+') as f:
                self.tasks = yaml.load(f)
        else:
            self.tasks = {}

    def _save_to_file(self):
        with open(FILEPATH, 'w+') as f:
            yaml.dump(self.tasks, f)

    def add_task(self, name, description, priority, due_hour=1):
        if name in self.tasks:
            print('Task with name: %s already exists' % name)
        new_task = [name, description, priority, due_hour]
        self.tasks.update({name: new_task})
        self._save_to_file()
    
    def delete_task(self, name):
        if name not in self.tasks.keys():
            print('Cannot delete a non-exist task %s' % name)
        self.tasks.pop(name, None)
        self._save_to_file()

    def display(self):
        if self.tasks:
            print('here are your tasks:')
            for v in self.tasks.values():
                print('%-20s %-10s %-10s %-50s' %(v[0], v[2], v[3],v[1]))

if __name__ == '__main__':

    schedule = Schedule()

    action = sys.argv[1]
    args = sys.argv[2:]

    def add(name, description, priority, due_hour):
        schedule.add_task(name, description, priority, due_hour)
        schedule.display()

    def delete(name):
        schedule.delete_task(name)
        schedule.display()

    def display():
        schedule.display()

    options = {
        'add': add,
        'delete': delete,
        'display': display
    }

    options[action](*args)
        

