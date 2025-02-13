#!/usr/bin/env python
import argparse
import pandas as pd
from scope.fritz import api


def manage_annotation(action, source, group_ids, token, origin, key, value):

    # Forgiving definitions of actions
    if action in ['update', 'Update', 'UPDATE']:
        action = 'update'
    elif action in ['delete', 'Delete', 'DELETE']:
        action = 'delete'
    elif action in ['post', 'Post', 'POST']:
        action = 'post'

    # Initial checks for origin and key, always necessary
    if origin is None:
        print('Error: please specify origin to %s' % action)
        return

    if key is None:
        print('Error: please specify key to %s' % action)
        return

    # check if source is single object or csv file of many
    if source.endswith('.csv'):
        file = pd.read_csv(source)  # modify input formats to prepare for loop
        if 'obj_id' not in file.columns:
            raise KeyError('CSV file must include column obj_id for ZTF source IDs.')
        obj_ids = file['obj_id']
        if (action == 'update') | (action == 'post'):
            values = file[key]
    else:
        obj_ids = [source]  # modify single source input formats to prepare for loop
        if value is not None:
            values = [float(value)]
        else:
            values = [value]

    # loop over objects, performing specified annotation action
    for i in range(len(obj_ids)):
        obj_id = obj_ids[i]

        # update and delete branches require GET for existing annotation
        if (action == 'update') | (action == 'delete'):
            matches = 0
            # get all annotations for object
            response = api("GET", '/api/sources/%s/annotations' % obj_id, token).json()
            data = response.get('data')

            # loop through annotations, checking for match with input key and origin
            for entry in data:
                annot_id = str(entry['id'])
                annot_origin = entry['origin']
                annot_data = entry['data']

                annot_name = [x for x in annot_data.keys()][0]
                annot_value = [x for x in annot_data.values()][0]

                # if match is found, perform action
                if (key == annot_name) & (origin == annot_origin):
                    matches += 1
                    if action == 'update':
                        value = values[i]

                        # Check value if performing update or post actions
                        if value is None:
                            raise ValueError(
                                'please specify annotation value to update or post.'
                            )

                        # After passing check, revise annotation with PUT
                        else:
                            json = {
                                "data": {key: value},
                                "origin": origin,
                                "obj_id": annot_id,
                            }
                            response = api(
                                "PUT",
                                '/api/sources/%s/annotations/%s' % (obj_id, annot_id),
                                token,
                                json,
                            )
                            if response.status_code == 200:  # success
                                print(
                                    'Updated annotation %s (%s = %s to %s) for %s'
                                    % (
                                        annot_origin,
                                        annot_name,
                                        annot_value,
                                        value,
                                        obj_id,
                                    )
                                )
                            else:
                                print('Did not %s - check inputs.' % action)

                    # Delete annotation with DELETE
                    elif action == 'delete':
                        response = api(
                            "DELETE",
                            '/api/sources/%s/annotations/%s' % (obj_id, annot_id),
                            token,
                        )
                        if response.status_code == 200:  # success
                            print(
                                'Deleted annotation %s (%s = %s) for %s'
                                % (annot_origin, annot_name, annot_value, obj_id)
                            )
                        else:
                            print('Did not %s - check inputs.' % action)

            # Alert user if no origin/key matches in each source's annotations
            if matches == 0:
                print(
                    'Origin/key pair %s/%s did not match any existing annotations for %s.'
                    % (origin, key, obj_id)
                )

        # if posting new annotation, skip search for exisiting ones
        elif action == 'post':
            value = values[i]

            # Check value if performing update or post actions
            if value is None:
                raise ValueError('please specify annotation value to update or post.')

            # After passing check, post annotation with POST
            else:
                json = {"origin": origin, "data": {key: value}, "group_ids": group_ids}
                response = api(
                    "POST", '/api/sources/%s/annotations' % obj_id, token, json
                )
                if response.status_code == 200:  # success
                    print(
                        'Posted annotation %s (%s = %s) for %s'
                        % (origin, key, value, obj_id)
                    )
                else:
                    print(
                        'Did not %s - check inputs and existing annotations.' % action
                    )

        # Must choose one of the three specified actions
        else:
            print(
                "Error: please specify action as one of 'post', 'update', or 'delete'."
            )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-action", help="post, update, or delete annotation")
    parser.add_argument("-source", help="Fritz object id or csv file of sources")
    parser.add_argument("-group_ids", type=int, nargs='+', help="list of group ids")
    parser.add_argument(
        "-token",
        type=str,
        help="put your Fritz token here. You can get it from your Fritz profile page",
    )
    parser.add_argument("-origin", type=str, help="name of annotation origin")
    parser.add_argument("-key", help="annotation key")
    parser.add_argument("-value", help="annotation value")

    args = parser.parse_args()

    manage_annotation(
        args.action,
        args.source,
        args.group_ids,
        args.token,
        args.origin,
        args.key,
        args.value,
    )
