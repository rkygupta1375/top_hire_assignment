# Backend assignment

    Backend assignment to filter out candidates listed in the database

## Dependecy:-

    `. Install django -> pip install Django==3.2.4`

## Run Script:-
        Run match_candidate.py script to check query output of 
        query -> input="""(Java AND Spring) OR (Python AND Django) OR (Ruby AND (Nodejs OR (ROR AND Mysql)))""", output="Mongodb Query"
        
        Edit match_candidate driver code to run other queries:
    `
        1) create class instance -> i.e
            query = m.get_candidates(input="""(Java AND Spring) OR (Python AND Django) OR (Ruby AND (Nodejs OR (ROR AND Mysql)))""", output="Mongodb Query")

        2) Print output of above class method to get output -> i.e
            print(query)
    `
