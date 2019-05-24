#!/usr/bin/env python
# Copyright (C) 2019 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import sys

# Converts the SQL metrics for trace processor into a C++ header with the SQL
# as a string constant to allow trace processor to exectue the metrics.

REPLACEMENT_HEADER = '''/*
 * Copyright (C) 2019 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 *******************************************************************************
 * AUTOGENERATED BY tools/gen_merged_sql_metrics - DO NOT EDIT
 *******************************************************************************
 */

 #include <string.h>
'''

NAMESPACE_BEGIN = '''
namespace perfetto {
namespace trace_processor {
namespace metrics {
namespace sql_metrics {
'''

FILE_TO_SQL_STRUCT = '''
struct FileToSql {
  const char* path;
  const char* sql;
};
'''

NAMESPACE_END = '''
}  // namespace sql_metrics
}  // namespace metrics
}  // namespace trace_processor
}  // namsepace perfetto
'''

def filename_to_variable(filename):
  return "k" + "".join([x.capitalize() for x in filename.split("_")])

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--cpp_out', required=True)
  parser.add_argument('sql_files', nargs='*')
  args = parser.parse_args()

  root_path = os.path.commonprefix(
    [os.path.abspath(x) for x in args.sql_files])

  # Extract the SQL output from each file.
  sql_outputs = {}
  for file_name in args.sql_files:
    with open(file_name, 'r') as f:
      relpath = os.path.relpath(file_name, root_path)
      sql_outputs[relpath] = "".join(
        x for x in f.readlines() if not x.startswith('--'))

  with open(args.cpp_out, 'w+') as output:
    output.write(REPLACEMENT_HEADER)
    output.write(NAMESPACE_BEGIN)

    # Create the C++ variable for each SQL file.
    for path, sql in sql_outputs.items():
      name = os.path.basename(path)
      variable = filename_to_variable(os.path.splitext(name)[0])
      output.write('\nconst char {}[] = R"gendelimiter(\n{})gendelimiter";\n'
        .format(variable, sql))

    output.write(FILE_TO_SQL_STRUCT)

    # Create mapping of filename to variable name for each variable.
    output.write("\nconst FileToSql kFileToSql[] = {")
    for path in sql_outputs.keys():
      name = os.path.basename(path)
      variable = filename_to_variable(os.path.splitext(name)[0])
      output.write('\n  {{"{}", {}}},\n'.format(path, variable))
    output.write("};\n")

    output.write(NAMESPACE_END)

  return 0

if __name__ == '__main__':
  sys.exit(main())
