
# Predicts if the given text should be printed as preformated or not
def shouldBePreFormatted(text):
    
    #Just check if there are spaces after new lines
    startingSpaces = 0
    newLine = True
    
    for ch in text:
        
        if ch is '\n':
            newLine = True
        
        elif newLine:
            
            if ch is ' ' or ch is '\t':
                startingSpaces += 1

            newLine = False

    if startingSpaces >= 4:
        return True
    else:
        return False    

        