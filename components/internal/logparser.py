import typing as t

from components.internal.util import Event, Test, make_test_end_event

# TODO: separate tests by files
# add analisable info (msg sizes etc)

class LogParser:
    def __init__(self) -> None:
        self.tests: t.Dict[str, Test] = {}

    def parse_log_file(self, file_path: str):
        with open(file_path, 'rt') as f:
            last_test_name = ''
            test_event_counter = 0
            node_ids = set()
            for line in f:
                line = line.strip()
                if not line:
                    # for last line (or any empty)
                    continue
                if line.startswith("NODE_IDS"):
                    node_ids = set(line.split(":")[1:])
                    continue
                if line.startswith("TEST_BEGIN"):
                    last_test_name = line.split(':', maxsplit=1)[1]
                    self.tests[last_test_name] = Test(last_test_name, [], None, None, [])
                    continue
                if line.startswith("TEST_END"):
                    _, status, err = line.split(':', maxsplit=2)
                    err = err if err else None
                    self.tests[last_test_name].status = status
                    self.tests[last_test_name].err = err
                    self.tests[last_test_name].node_ids = node_ids
                    self.tests[last_test_name].events.append(make_test_end_event(test_event_counter))
                    test_event_counter = 0
                    continue

                self.tests[last_test_name].events.append(Event.from_json(line, test_event_counter))
                test_event_counter += 1


        if len(self.tests) == 0:
            raise RuntimeError(
                f'Parsed empty data. Tests: {len(self.tests)} '
            )