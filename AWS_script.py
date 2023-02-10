import json
import sys
import boto3

def detect_text(photo, bucket):

    client=boto3.client(service_name='rekognition',region_name='us-east-1',
                        aws_access_key_id='', aws_secret_access_key='')


    #REPLACE access_key_id and secret_access_key with other values.


    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':photo}}, Filters={'WordFilter':{'MinConfidence':85, 'MinBoundingBoxHeight':0.02}})
                        

    data = {
        'source': photo,
        'data': response['TextDetections']
        }

    values = []
    skipped = 0
    data_coordinates = []

    for i in range(len(data['data'])):
        if(data['data'][i]['Type'] == "LINE"):                      #Only taking full lines in order to keep name as one string.
            if (data['data'][i]['DetectedText'] != 'SWOOPS'):       #Skipping SWOOPS logos, if any show up.
                text = data['data'][i]['DetectedText']
                
                x = data['data'][i]['Geometry']['BoundingBox']['Left'] + (data['data'][i]['Geometry']['BoundingBox']['Width'])/2

                y = data['data'][i]['Geometry']['BoundingBox']['Top'] + (data['data'][i]['Geometry']['BoundingBox']['Height'])/2
                
                data_coordinates.append((text, x, y))               #Tuple with text and textbox center coordinates.


    curr_x = 0
    curr_y = 0
    min_y = 0.99
    val_idx = 0

    for i in range(len(data_coordinates)):
        curr_y = data_coordinates[i][2]
        if(curr_y < min_y):
            val_idx = i
            min_y = curr_y

    values.append(data_coordinates[val_idx][0])

    attributes = ["3PT", "2PT-INT", "2PT-MID", "FT", "DREB", "OREB", "PASS", "IDEF", "PDEF", "PHY", "LONG", "HSTL", "IQ", "LDRS", "COACH"]      #List of all 15 attributes, in order.

    for att in attributes:
        curr_x = 0.0
        curr_y = 0.0
        min_y = 1.1
        val_idx = 0

        for a in range(len(data_coordinates)):              #Finding the coordinates of the attribute header textbox.
            if(str(data_coordinates[a][0]) == str(att)):
                curr_x = data_coordinates[a][1]
                curr_y = data_coordinates[a][2]

        if(curr_x == 0.0) and (curr_y == 0.0) and (str(att) == "IQ"):       #AWS Rekognition does not recognize IQ with trophy for some reason. This is clear in the AWS demo itself.
            curr_x = 0.52267456                                             #I noted down the coordinates generated on other images and used those to prevent the values from staying at 0.0.
            curr_y = 0.81054687

        for b in range(len(data_coordinates)):
            if((curr_x - data_coordinates[b][1]) < 0.04) and ((data_coordinates[b][1] - curr_x) < 0.04):        #Checking for very similar x-values (same column).
                if ((data_coordinates[b][2] - curr_y) > 0.0001) and ((data_coordinates[b][2] - curr_y) < min_y):    #Checking for least difference y-value textbox below header.
                    val_idx = b
                    min_y = data_coordinates[b][2] - curr_y

        #print(str(att) + " : ")
        #print("x = " + str(curr_x))
        #print("y = " + str(curr_y))
        #print("value = " + str(data_coordinates[val_idx][0]))

        values.append(data_coordinates[val_idx][0])

    return values

def cross_check(values, player):
    
    flag = True
    
    if(values[0] != player['name']):
        flag = False
        
    else:
        print(str(values[0]) + ' == ' + str(player['name']))
        attributes = []
        for i in range(15,30):
            if(player['attributes'][i]['value'] == None):
                attributes.append('??') #Replacing null values with "??" in attributes extracted from json.
            else:
                attributes.append(round(player['attributes'][i]['value'])) #Rounding attribute data to nearest integer to match with image values.

        temp = attributes[7]        #Moving physicality value down by two values to reflect the image table.
        attributes[7] = attributes[8]
        attributes[8] = attributes[9]
        attributes[9] = temp

        for j in range(1,16):
            print(str(values[j]) + ' == ' + str(attributes[j-1]))
            if(str(values[j]) != str(attributes[j-1])):
                flag = False

    return flag


def main():
    args = sys.argv[1:]
    bucket='swoops-pictures'
    photo= str(args[0]) + '_back_card.png'
    file = open(str(args[0]) + '_player.json')
    player_data = json.load(file)
    file.close()

    img_values = detect_text(photo,bucket)

    #cross_check(img_values, player_data)
    print(cross_check(img_values, player_data))
    


if __name__ == "__main__":
    main()
    
