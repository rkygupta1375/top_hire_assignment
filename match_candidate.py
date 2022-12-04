import re 
from django.db.models import Q

class MatchCandidate:

    def __init__(self):
        pass

    def split_convert(self, input, start):
        """
            Required input -> input_array, start(to check level of parenthesis)
            This method convert input into a common format which is used to create different queries based on db
            Output -> return input_array and operator_array

        """
        operator_array = []
        input_array = []
        if re.search("\)\s*OR\s*\(", input):
            split_list = re.split("\)\s*OR\s*\(",input)
            split_list = [item.strip() for item in split_list]
            for index,item in enumerate(split_list):
                if item.startswith("("):
                    item = item[1:]
                if item.endswith(")"):
                    item = item[:-1]
                item = "("+item+")"
                out,oper = self.split_convert(item, start+1)
                if len(out) > 0:
                    input_array.extend(out) if start > 0 else input_array.append(out)
                else:
                    input_array.extend([item])

                if oper:
                    if start > 0:
                        operator_array.extend(oper)
                    else:
                        if index < len(split_list)-1:
                            operator_array.append(['|',*oper])  
                        else:
                            operator_array.append([*oper])
                else:
                    if item != split_list[-1]:
                        if start==0:
                            operator_array.append(['|'])
                        else:
                            operator_array.append('|')
        elif re.search("\)\s*AND\s*\(", input):
            split_list = re.split("\)\s*AND\s*\(",input)
            split_list = [item.strip() for item in split_list]
            for index,item in enumerate(split_list):
                if item.startswith("("):
                    item = item[1:]
                if item.endswith(")"):
                    item = item[:-1]
                item = "("+item+")"
                out,oper = self.split_convert(item, start+1)
                if len(out) > 0:
                    input_array.extend(out) if start > 0 else input_array.append(out)
                else:
                    input_array.extend([item])

                if oper:
                    if start > 0:
                        operator_array.extend(oper)
                    else:
                        if index < len(split_list)-1:
                            operator_array.append(['&',*oper])  
                        else:
                            operator_array.append([*oper])
                else:
                    if item != split_list[-1]:
                        if start==0:
                            operator_array.append(['&'])
                        else:
                            operator_array.append('&')

        elif re.search("\(*\)*\w*\s+OR\s+\w*\(*\)*", input) or re.search("\(*\)*\w*\s+AND\s+\w*\(*\)*", input):
            xor = re.search("\(*\)*\w*\s+OR\s+\w*\(*\)*", input)
            xand = re.search("\(*\)*\w*\s+AND\s+\w*\(*\)*", input)
            finder = None
            operator = ''
            if xor and xand:
                xor_start = xor.start()
                xand_start = xand.start()
                if xor_start < xand_start:
                    finder = xor
                else:
                    finder = xand
            
            if not finder:
                split_list = re.split("\s+OR\s+",input,1) if xor else re.split("\s+AND\s+",input,1)
                operator = '|' if xor else '&'
            else:
                split_list = re.split("\s+OR\s+",input,1) if finder == xor else re.split("\s+AND\s+",input,1)
                operator = '|' if finder == xor else '&'

            for index, item in enumerate(split_list):
                if item.startswith('('):
                    item = item[1:]
                if item.endswith(")"):
                    item = item[:-1]
                out,oper = self.split_convert(item, start+1)
                if len(out) > 0:
                    input_array.extend(out) if start > 0 else input_array.append(out)
                else:
                    input_array.extend([item])

                if oper:
                    if start > 0:
                        operator_array.extend(oper)
                    else:
                        if index < len(split_list)-1:
                            operator_array.append([operator,*oper])  
                        else:
                            operator_array.append([*oper])
                else:
                    if index < len(split_list)-1:
                        if start==0:
                            operator_array.append([operator])
                        else:
                            operator_array.append(operator)
        else:
            return([input],[])

        
        return (input_array,operator_array)

    def sql_formatter(self, input_array, operator_array):
        """
            Required input -> input_array, operator_array
            This method create a sql query based on input and operator array
            Output -> return a query suitable for sql database

        """
        filtering = ""
        dic = {'&':'and','|':'or'}
        if not operator_array:
            filtering = f"""(lower(text) like '% {input_array[0]} %')"""
        else:
            if len(operator_array) != len(input_array):
                operator_array.append([])
            for input,operator in zip(input_array,operator_array):
                index = len(input) -1
                op_index = len(operator) - 1
                queue = ""
                while index > 0:
                    if not queue:
                        x=(f"""(lower(text) like '% {input[index]} %')""")
                        y=(f"""(lower(text) like '% {input[index-1]} %')""")
                        op = operator[op_index]
                        queue += f"""({x} {dic[op]} {y})"""
                        index -= 2
                        op_index -= 1
                    else:
                        x= f"""(lower(text) like '% {input[index]} %')"""
                        op = operator[op_index]
                        queue += f"""{dic[op]} {x}"""
                        queue = '('+queue+')' 
                        index -= 1
                        op_index -=1
                if index == 0:
                    x=f"""(lower(text) like '% {input[index]} %')"""
                    if not queue:
                        filtering += f"""{x} {dic[operator[op_index]]} """ if operator else x
                    else:
                        filtering += f"""{queue} {dic[operator[op_index]]} ({x}) """
                        op_index -= 1
                        if op_index == 0:
                            filtering += f""" {dic[operator[op_index]]} """
                else:
                    if op_index == 0:
                        filtering += f"""{queue} {dic[operator[op_index]]} """
                    else:
                        filtering += f""" {queue} """

        return f"""select id,name from resume where {filtering}"""

    def orm_formatter(self, input_array, operator_array):
        """
            Required input -> input_array, operator_array
            This method create a django based ORM query based on input and operator array
            Output -> return a query suitable for Django ORM

        """

        filtering = ""
        if not operator_array:
            filtering = f"""{Q}(text__icontains=={input_array[0]})"""
        else:
            if len(operator_array) != len(input_array):
                operator_array.append([])
            for input,operator in zip(input_array,operator_array):
                index = len(input) -1
                op_index = len(operator) - 1
                queue = ""
                while index > 0:
                    if not queue:
                        x=(f"""{Q}(text__icontains={input[index]})""")
                        y=(f"""{Q}(text__icontains={input[index-1]})""")
                        op = operator[op_index]
                        queue += f"""({x} {op} {y})"""
                        index -= 2
                        op_index -= 1
                    else:
                        x= f"""{Q}(text__icontains={input[index]})"""
                        op = operator[op_index]
                        queue += f"""{op} {x}"""
                        queue = '('+queue+')' 
                        index -= 1
                        op_index -=1
                if index == 0:
                    x=f"""{Q}(text__icontains={input[index]})"""
                    if not queue:
                        filtering += f"""{x} {operator[op_index]} """ if operator else x
                    else:
                        filtering += f"""{queue} {operator[op_index]} ({x}) """
                        op_index -= 1
                        if op_index == 0:
                            filtering += f""" {operator[op_index]} """
                else:
                    if op_index == 0:
                        filtering += f"""{queue} {operator[op_index]} """
                    else:
                        filtering += f"""{queue} """

        
        return f"""Resume.objects.filter({filtering})"""

    def mongo_formatter(self, input_array, operator_array):
        """
            Required input -> input_array, operator_array
            This method create a mongo query based on input and operator array
            Output -> return a query suitable for mongodb

        """
        filtering = {}
        operator_dic =  {'&':'and','|':'or'}
        if not operator_array:
            filtering = {"text": {"$regex": input_array[0], "$options":"i"}}
        else:
            last_key = new_key = ""
            if len(operator_array) != len(input_array):
                operator_array.append([])
            for input,operator in zip(input_array,operator_array):
                index = len(input) -1
                op_index = len(operator) - 1
                queue = ""
                inner_dict = {}

                while index > 0:
                    if not inner_dict:
                        x={"text": {"$regex": input[index], "$options":"i"}}
                        y={"text": {"$regex": input[index-1], "$options":"i"}}
                        inner_dict = {
                            "$"+operator_dic[operator[op_index]]:[x,y]
                        }

                        index -= 2
                        op_index -= 1
                    else:
                        x={"text": {"$regex": input[index], "$options":"i"}}
                        op = operator[op_index]
                        inner_dict = {
                            "$"+operator_dic[operator[op_index]]:[inner_dict,x]
                        } 
                        index -= 1
                        op_index -=1

                if index == 0:
                    x={"text": {"$regex": input[index], "$options":"i"}}
                    if not inner_dict:
                        mediator = x
                        if op_index == 0:
                            new_key = "$"+operator_dic[operator[op_index]]
                            if not filtering:
                                if new_key != last_key:
                                    last_key = new_key
                                    filtering[last_key] = []
                                filtering[new_key].append(x)
                            else:
                                filtering[last_key].append(x)
                                if new_key != last_key:
                                    last_key = new_key
                                    filtering[last_key] = []
                            op_index -= 1

                    else:
                        mediator = {"$"+operator_dic[operator[op_index]]:[inner_dict,x]}
                        index -= 1
                        op_index -= 1
                        if not filtering:
                            filtering = mediator
                        else:
                            filtering[last_key].append(mediator)
                        
                        if op_index == 0:
                            new_key = "$"+operator_dic[operator[op_index]]
                            if new_key != last_key:
                                last_key = new_key
                                filtering[last_key] = []
                            op_index -= 1
                            
                else:
                    if not filtering:
                        filtering = {
                            "$"+operator_dic[operator[op_index]]:[inner_dict]
                        }
                        last_key = "$"+operator_dic[operator[op_index]]
                        op_index -= 1
                    else:
                        filtering[last_key].append( {
                            "$"+operator_dic[operator[op_index]]:[inner_dict]
                        })
                        op_index -= 1
                        if op_index == 0:
                            new_key = "$"+operator_dic[operator[op_index]]
                            if new_key != last_key:
                                last_key = new_key
                                filtering[last_key] = []
                            op_index -= 1
                        
        return f"""db.resume.find({filtering})"""

    def get_candidates(self, input: str="", output: str="Raw SQL"):

        """
            This method filter out candidates on based of input_query.
            Input Type ->>   String
            Output Type ->> String
            Output Info-> This method return query in different format based on database 

        """
        if input == "":
            return {
                "message": "user should provide some input to search on",
                "output": None
            }
        else:
            # using split_convert method to generate a common pattern before giving to output formatter methods.
            input_array,operator_array  = self.split_convert(input, start=0)

            if output == "Raw SQL":
                out = self.sql_formatter(input_array,operator_array)
            elif output == "ORM Queryset":
                out = self.orm_formatter(input_array,operator_array)
            else:
                out = self.mongo_formatter(input_array,operator_array)
            
            return out


if __name__ == '__main__':

    m = MatchCandidate()
    # query = m.get_candidates(input="""(Java AND Spring) OR (Python AND Django) OR (Ruby AND (Nodejs OR (ROR AND Mysql)))""")
    # query = m.get_candidates(input="""(Java AND Spring) OR (Python AND Django) OR (Ruby AND (Nodejs OR (ROR AND Mysql)))""",
    #                         output="ORM Queryset")
    query = m.get_candidates(input="""(Java AND Spring) OR (Python AND Django) OR (Ruby AND (Nodejs OR (ROR AND Mysql)))""",
                            output="Mongodb Query")
    # query = m.get_candidates(input="""java """)
    # query = m.get_candidates(input="""java """,output="ORM Queryset")
    # query = m.get_candidates(input="""java """,output="Mongodb Query")
    # query = m.get_candidates(input="""Java AND ("Ruby on Rails" OR (Python AND Django))""")
    # query = m.get_candidates(input="""Java AND ("Ruby on Rails" OR (Python AND Django))""",output="ORM Queryset")
    # query = m.get_candidates(input="""Java AND ("Ruby on Rails" OR (Python AND Django))""",output="Mongodb Query")
    print(query)
    