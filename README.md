Welcome to Thunderdome!

This program will work flawlessly provided the necessary dependencies are installed. To identify those quickly, simply attempt to execute this using `python3 power_supplies.py` and address the dependency gaps as they are identified by python.

Once you have all of the necessary python dependencies, you will need to install and configure postgres. This program is intrinsically tied to postgres, and will not run without it. You will need - at a minimum - two tables in your database: measurements and ps_info. Measurements contains the actual values as they are parsed from your power supply. Ps_info contains the information on each power supply connected and the details of what each channel is powering. NOTE: 'Not Connected' is a perfectly acceptable entry. Here is the proper output from the measurements table:

<database_name_here>=# \d measurements
                    Table "public.measurements"
 Column |           Type           | Collation | Nullable | Default 
--------+--------------------------+-----------+----------+---------
 time   | timestamp with time zone |           | not null | 
 psid   | integer                  |           |          | 
 c1_v   | real                     |           |          | 
 c1_i   | real                     |           |          | 
 c1_w   | real                     |           |          | 
 c2_v   | real                     |           |          | 
 c2_i   | real                     |           |          | 
 c2_w   | real                     |           |          | 
 c3_v   | real                     |           |          | 
 c3_i   | real                     |           |          | 
 c3_w   | real                     |           |          | 

NOTE: there is no id or primary key in this table, though timestamp may not be null.

Here is the proper output from the ps_info table:


<database_name_here>=# \d ps_info
                   Table "public.ps_info"
 Column |       Type        | Collation | Nullable | Default 
--------+-------------------+-----------+----------+---------
 psid   | integer           |           |          | 
 name   | character varying |           |          | 
 c1     | character varying |           |          | 
 c2     | character varying |           |          | 
 c3     | character varying |           |          | 

NOTE: there is also no id or primary key in this table.

Once you have both of those tables setup, you need to populate the ps_info table with all of the information on all power supplies connected to the host laptop. Use the `read_power_supplies.sh` script to print out the information on each supply. Omit the first four characters of the serial number when entering the value into the ps_info table.

For help with installing and configuring postgres, reference the following resources:

https://www.cherryservers.com/blog/how-to-install-and-setup-postgresql-server-on-ubuntu-20-04
https://www.tutorialsteacher.com/postgresql/insert-into-table

With postgres setup, edit `power_supplies.py` to identify the number of power supplies connected, and update the postgres connection information with the specifics of your postgres configuration.

After you have completed these items, you are free to use this to monitor and log all information on the power supply usage using `python3 power_supplies.py`.
