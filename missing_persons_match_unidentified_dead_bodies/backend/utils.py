from io import BytesIO

import cv2
import numpy as np
import regex as re
from django.core.files.uploadedfile import InMemoryUploadedFile


# Returns resized for upload and for icon
def resize_image(file, size_image, size_icon):
    print(size_image)
    # Open the uploaded file as an image
    image = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    # Get the aspect ratio of the image
    aspect_ratio = float(image.shape[1]) / image.shape[0]

    # Compute the new dimensions of the image
    new_height = int(size_image)
    new_width = int(new_height * aspect_ratio)

    icon_height = int(size_icon)
    icon_width = int(icon_height * aspect_ratio)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    image_icon = cv2.resize(resized_image, (icon_width, icon_height))

    # Encode the resized image
    ret, image_buffer = cv2.imencode(".jpg", resized_image)
    image_buffer = BytesIO(image_buffer)
    resized_image = InMemoryUploadedFile(
        image_buffer,
        None,
        file.name,
        "image/jpeg",
        image_buffer.getbuffer().nbytes,
        None,
    )
    # Icon
    ret, icon_buffer = cv2.imencode(".jpg", image_icon)
    icon_buffer = BytesIO(icon_buffer)
    image_icon = InMemoryUploadedFile(
        icon_buffer,
        None,
        "icon_" + file.name,
        "image/jpeg",
        icon_buffer.getbuffer().nbytes,
        None,
    )
    return (resized_image, image_icon)


def tokenize(text):
    stopwords = {
        word.strip()
        for word in """no,off,her,with,myself,it's,all,m,those,ain,be,mustn,theirs,against,
            being,on,wouldn't,that,wasn,more,mightn't,it,himself,only,couldn,isn,down,
            or,then,they,we,until,d,didn,wasn't,out,doesn't,than,by,don,won't,in,during,
            as,do,so,has,she's,further,through,when,themselves,shan,don't,ma,y,there,
            can,you'd,weren,its,isn't,having,most,i,itself,aren't,doing,now,you've,our,
            needn't,ve,me,wouldn,below,such,if,them,for,were,why,his,weren't,did,him,
            herself,own,re,where,my,shouldn,o,ll,over,an,above,haven,she,does,at,nor,
            too,you'll,because,each,am,the,hadn,didn't,just,should've,what,these,but,
            not,hers,which,have,a,again,couldn't,under,up,hadn't,hasn't,before,that'll,
            is,your,any,between,aren,into,needn,ours,shan't,will,he,how,few,shouldn't,
            you're,been,mightn,once,doesn,t,are,here,was,same,mustn't,after,s,
            yourselves,of,other,their,whom,had,from,some,yours,while,won,to,you,who,
            yourself,very,should,ourselves,both,haven't,this,about,and,hasn,www,
            mandal,fox,rs,manupatra,com""".split(
            ","
        )
    }

    def remove_stop(tokens):
        return [t.lower() for t in tokens if t.lower() not in stopwords]

    def tokenize(text):
        return re.findall(r"[\w-]*\p{L}[\w-]*", text)

    return remove_stop(tokenize(text))
