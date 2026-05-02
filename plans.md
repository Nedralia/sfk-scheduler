# Plans

Here are outlined the future plans for the project.

## API

An API is needed to communicate and make changes to the schedule.

Examples of possible uses of the API:

1. Register that an assignment has been completed
2. Send photos as proof of the job done
3. Trigger re-generation of a cleaning schedule
4. Swap people who are assigned on a specific week

## Features

### Swapping places

One person initiates that they want another member to be assigned to a specific week instead of someone else.

The new assignee is sent an email of the request.

The person receiving the request has to confirm it by clicking on a link in the mail they receive.

Have a protection against spam.

### Push mail

Send out a mail as a reminder before a cleaning assignment.

Also, if a person has not yet registered their own assignment as done, send an email reminder for them to do so.

!!! Need to calculate the previous schedules !!!
They go in alphabetic order so just need to know who it is on the current week and go backwards.
Would be nice to have a script to do this.
