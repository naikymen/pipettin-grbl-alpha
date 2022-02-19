# MongoDB default documents

- Platforms
- Workspaces
- Protocols

## export

    mongoexport -d <database> -c <collection_name> -o <output_file.json> --jsonArray

Examples:

    mongoexport -d pipettin -c platforms -o platforms_export.json --jsonArray

## import

In the Raspberry Pi 4 I had to append `--jsonArray` to these commands to fix the  following error: `BSON representation of supplied JSON is too large`

In my PC this was unnecesary, it's probably due to the old mongodb version on raspbian.

```bash
mongoimport --db pipettin --collection platforms --file platforms.json --jsonArray
mongoimport --db pipettin --collection platforms --file platforms_enanas.json --jsonArray
mongoimport --db pipettin --collection workspaces --file workspaces.json --jsonArray
mongoimport --db pipettin --collection protocols --file protocols.json --jsonArray
mongoimport --db pipettin --collection protocols --file protocols_for_tests.json --jsonArray
mongoimport --db pipettin --collection protocols --file protocol_test1.json --jsonArray
```

Can check with:

```
$ mongo
> use pipettin
> db.workspaces.find().pretty()
> db.protocols.find().pretty()
```

## update

Drop tables from mongo and reimport them using the commands above.

```
$ mongo
> use pipettin
> db.platforms.drop()
> db.protocols.drop()
> db.workspaces.drop()
$ git pull
$ mongoimport --db pipettin --collection platforms --file defaults/platforms.json
```

## troubleshooting

You may need to set "export LC_ALL=C" in bash if you get the following error:

    BadValue Invalid or no user locale set. Please ensure LANG and/or LC_* environment variables are set correctly

See: https://stackoverflow.com/questions/26337557/badvalue-invalid-or-no-user-locale-set-please-ensure-lang-and-or-lc-environme
