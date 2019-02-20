#############################
#############################
#############################
#############################
####
####  Multitasking experiment: Typing digits (keyboard) while tracking (joystick)
####  Developed by Christian P. Janssen, c.janssen@ucl.ac.uk
####  December 2009 - March 2010
####
####
####
####
#############################
#############################
#############################
import inspect
import math
import os
import random
import time
import pygame
import scipy
import scipy.special

######initialize global variables

incorrectDigits = 0
correctDigits = 0
duringTrialScore = 0
outsideRadius = False
visitDigits = 0
visitIncorrectDigits = 0
intermediateScoreVisit = 0
visitScore = 0
visitTime = 0
visitEndTime = 0
visitStartTime = 0
writeMaxDistance = 0
writeMeanDistance = 0
writeEndDistance = 0
writeStartDistance = 0

firstTrial = ""

global penalty
penalty = ""

timeFeedbackIsGiven = 4

global EnvironmentIsRunning  # True if there is a display
global joystickObject  # the joystick object (initialized at start of experiment)
global partOfExperiment
partOfExperiment = "singleTaskTracking"
global outputFile
global summaryOutputFile
global conditions
conditions = ()
cursorMotion = (0, 0)  # the motion of the joystick
trackerdistanceArray = []
digitPressTimes = []
startTime = 0
timeFeedbackIsShown = 5

startedClosingThreads = False

backgroundColorTrackerScreen = (255, 255, 255)  # white
backgroundColorDigitScreen = backgroundColorTrackerScreen
backgroundColorEntireScreen = (50, 50, 50)  # gray
coverUpColor = (200, 200, 200)  # very light gray
TrackerTargetColor = (0, 0, 0)  # black
radiusInnerColor = (255, 204, 102)  # orange
radiusOuterColor = (255, 0, 0)  # red
CursorColor = (0, 0, 255)  # blue

ExperimentWindowSize = (1280, 1024)  # eye-tracker screen: 1280*1024 pixels
TrackingTaskWindowSize = DigitTaskWindowSize = (450, 450)
TrackerTargetSize = CursorSize = (20, 20)

topLeftCornerOfDigitTaskWindow = (
    int(ExperimentWindowSize[0] - TrackingTaskWindowSize[0] - DigitTaskWindowSize[0]) / 3, 50)
topLeftCornerOfTrackingTaskWindow = (2 * topLeftCornerOfDigitTaskWindow[0] + DigitTaskWindowSize[0], 50)

topLeftCornerOfGoalNumber = (DigitTaskWindowSize[0] / 2 - 150 + topLeftCornerOfDigitTaskWindow[0],
                             DigitTaskWindowSize[1] / 2 - 20 + topLeftCornerOfDigitTaskWindow[1])
topLeftCornerOfUserNumber = (DigitTaskWindowSize[0] / 2 - 150 + topLeftCornerOfDigitTaskWindow[0],
                             DigitTaskWindowSize[1] / 2 + 20 + topLeftCornerOfDigitTaskWindow[1])
numberCompleted = False  # boolean: did user completely type in the number?
goalNumber = "123456789"
userNumber = ""
lengthOfGoalNumber = 27

scoresOnThisBlock = []  # stores the scores on the current block. Can be used to report performance each 5th trial

numbersAvailableForGoalNumber = "123456789"
TrackerTargetCoordinates = (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] / 2,
                            topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] / 2)
CursorCoordinates = (
    TrackingTaskWindowSize[0] / 2 - (CursorSize[0] / 2), TrackingTaskWindowSize[1] / 2 - (CursorSize[0] / 2))

fontsizeGoalAndUserNumber = 30

maxTrialTimeDual = 30  # maximum time for dual-task trials 
maxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
maxTrialTimeSingleTyping = 20  # maximum time for single-task typing

numberOfDualTaskTrials = 40
numberOfSingleTaskTrackingTrials = 2
numberOfSingleTaskTypingTrials = 2

trackingWindowVisitCounter = 0
digitWindowVisitCounter = 0

trackingTaskPresent = True
digitTaskPresent = True

scalingCursorMotion = 5  # how many pixels does the cursor move when joystick is at full angle (value of 1 or -1).

global currentCondition
currentCondition = ""
global blockNumber
blockNumber = 0

global trialNumber
trialNumber = 0

global subjNr
subjNr = 0

global trackerWindowVisible
trackerWindowVisible = True
global digitWindowVisible
digitWindowVisible = True

radiusAroundTarget = 100

standardDeviationOfNoise = -1

stepSizeOfTrackerScreenUpdate = 0.005  # how many seconds does it take for a screen update?

scoresForPayment = []

baseratePayment = 0
maxPayment = 15  # what do we pay maximum?

mousePressed = False  # used at beginning of experiment: mouse needs to be clicked

timeOfCompleteStartOfExperiment = 0  # this value is needed because otherwise one of the time output numbers becomes too large to have enough precision


def writeSummaryDataToFile():
    print("FUNCTION: " + getFunctionName())
    global summaryOutputFile
    global subjNr
    global numberCompleted
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global userNumber
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global blockNumber
    global trialNumber
    global TrackerTargetCoordinates
    global CursorCoordinates
    global cursorMotion
    global startTime  # stores time at which trial started
    global trackerWindowVisible
    global digitWindowVisible
    global radiusAroundTarget
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment  # time at which experiment started
    global visitScore
    global visitDigits
    global visitIncorrectDigits
    global visitTime
    global outsideRadius
    global writeMaxDistance
    global writeMeanDistance
    global writeEndDistance
    global writeStartDistance

    summaryOutputText = str(subjNr) + " " + str(blockNumber) + " " + str(
        trialNumber) + " " + partOfExperiment + " " + str(standardDeviationOfNoise) + " " + str(visitTime) + " " + str(
        visitDigits) + " " + str(visitIncorrectDigits) + " " + str(visitScore) + " " + str(outsideRadius) + " " + str(
        writeMaxDistance) + " " + str(writeMeanDistance) + " " + str(writeEndDistance) + " " + str(
        writeStartDistance) + "\n"

    summaryOutputFile.write(summaryOutputText)
    print(summaryOutputText)


def writeDataToFile(Eventmessage1, message2):
    print("FUNCTION: " + getFunctionName())
    global outputFile
    global subjNr
    global numberCompleted
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global userNumber
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global blockNumber
    global trialNumber
    global TrackerTargetCoordinates
    global CursorCoordinates
    global cursorMotion
    global startTime  # stores time at which trial started
    global trackerWindowVisible
    global digitWindowVisible
    global radiusAroundTarget
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment  # time at which experiment started

    outputCursorCoordinates = CursorCoordinates
    outputTrackerTargetCoordinates = TrackerTargetCoordinates
    outputuserNumber = userNumber
    outputgoalNumber = goalNumber

    currentTime = time.time() - timeOfCompleteStartOfExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracker)
    currentTime = scipy.special.round(currentTime * 10000) / 10000

    localTime = time.time() - startTime  # this is a local time (reset at the start of each trial)
    localTime = scipy.special.round(localTime * 10000) / 10000

    if not trackingTaskPresent:
        outputCursorCoordinates = (-987654321, -987654321)  # keep it in number format to make later analysis easier :-)
        outputTrackerTargetCoordinates = (-987654321, -987654321)
        outputcursorMotion = (-987654321, -987654321)
        outputCursorDistance = (-987654321, -987654321, -987654321)  # (horiz, vert, straight line)
    else:
        outputCursorCoordinates = (scipy.special.round(outputCursorCoordinates[0] * 100) / 100,
                                   scipy.special.round(outputCursorCoordinates[1] * 100) / 100)
        outputTrackerTargetCoordinates = (scipy.special.round(outputTrackerTargetCoordinates[0] * 100) / 100,
                                          scipy.special.round(outputTrackerTargetCoordinates[1] * 100) / 100)

        outputcursorMotion = (
            scipy.special.round(cursorMotion[0] * 1000) / 1000, scipy.special.round(cursorMotion[1] * 1000) / 1000)

        distanceXY = (abs(outputTrackerTargetCoordinates[0] - outputCursorCoordinates[0]),
                      abs(outputTrackerTargetCoordinates[1] - outputCursorCoordinates[1]))

        distanceDirect = math.sqrt((distanceXY[0]) ** 2 + (distanceXY[1]) ** 2)
        distanceDirect = scipy.special.round(distanceDirect * 100) / 100

        outputCursorDistance = (distanceXY[0], distanceXY[1], distanceDirect)

    if not digitTaskPresent:
        outputuserNumber = -10
        outputgoalNumber = -10
        outputLengthOfUserNumber = 0
        outputLengthofGoalNumber = 0
    else:
        outputLengthOfUserNumber = len(userNumber)
        outputLengthofGoalNumber = len(goalNumber)

    if outputuserNumber == "":
        outputuserNumber = -10

    if partOfExperiment != "dualTask":
        pass

    ###still add the current condition

    outputText = str(subjNr) + " " + str(currentTime) + " " + str(localTime) + " " + str(blockNumber) + " " + str(
        trialNumber) + " " + partOfExperiment + " " + str(trackingTaskPresent) + " " + str(
        digitTaskPresent) + " " + str(trackerWindowVisible) + " " + str(digitWindowVisible) + " " + str(
        trackingWindowVisitCounter) + " " + str(digitWindowVisitCounter) + " " + str(radiusAroundTarget) + " " + str(
        standardDeviationOfNoise) + " " + str(outputCursorDistance[0]) + " " + str(outputCursorDistance[1]) + " " + str(
        outputCursorDistance[2]) + " " + str(outputCursorCoordinates[0]) + " " + str(
        outputCursorCoordinates[1]) + " " + str(outputTrackerTargetCoordinates[0]) + " " + str(
        outputTrackerTargetCoordinates[1]) + " " + str(outputcursorMotion[0]) + " " + str(
        outputcursorMotion[1]) + " " + str(outputuserNumber) + " " + str(outputgoalNumber) + " " + str(
        numberCompleted) + " " + str(outputLengthOfUserNumber) + " " + str(outputLengthofGoalNumber) + " " + str(
        Eventmessage1) + " " + str(message2) + "\n"

    outputFile.write(outputText)


def checkKeyPresses():
    print("FUNCTION: " + getFunctionName())
    global TrackerTargetCoordinates
    global CursorCoordinates
    global trackerdistanceArray
    global numberCompleted
    global startTime
    global app
    global startedClosingThreads
    global screen
    global digitPressTimes  # stores the intervals between keypresses
    global numberCompleted
    global goalNumber
    global userNumber
    global joystickObject  # the joystick object
    global cursorMotion
    global DigitTaskWindowSize
    global mousePressed
    global incorrectDigits
    global correctDigits
    global visitDigits
    global visitIncorrectDigits

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_app()
            return
        elif event.type == pygame.JOYAXISMOTION:
            if trackingTaskPresent:
                # values between -1 and 1. (-1,-1) top left corner, (1,-1) top right; (-1,1) bottom left, (1,1) bottom right
                measuredMotion = (joystickObject.get_axis(0), joystickObject.get_axis(1))
                cursorMotion = (measuredMotion[0], measuredMotion[1])
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 0:  # only respond to 0 button
                switchWindows("closeTracking")
                writeDataToFile("ButtonRelease", "none")
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeDataToFile("ButtonPress", "none")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePressed = True
            pos = pygame.mouse.get_pos()
            print(pos)
            posString = str(pos[0]) + "_" + str(pos[1])
            writeDataToFile("MousePress", posString)

        elif event.type == pygame.KEYDOWN:
            keycode = event.key
            if digitTaskPresent and keycode != "":
                localValue = ""
                if keycode == pygame.K_0 or keycode == pygame.K_KP0:
                    localValue = "0"
                elif keycode == pygame.K_1 or keycode == pygame.K_KP1:
                    localValue = "1"
                elif keycode == pygame.K_2 or keycode == pygame.K_KP2:
                    localValue = "2"
                elif keycode == pygame.K_3 or keycode == pygame.K_KP3:
                    localValue = "3"
                elif keycode == pygame.K_4 or keycode == pygame.K_KP4:
                    localValue = "4"
                elif keycode == pygame.K_5 or keycode == pygame.K_KP5:
                    localValue = "5"
                elif keycode == pygame.K_6 or keycode == pygame.K_KP6:
                    localValue = "6"
                elif keycode == pygame.K_7 or keycode == pygame.K_KP7:
                    localValue = "7"
                elif keycode == pygame.K_8 or keycode == pygame.K_KP8:
                    localValue = "8"
                elif keycode == pygame.K_9 or keycode == pygame.K_KP9:
                    localValue = "9"
                elif keycode == pygame.K_BACKSPACE or keycode == pygame.K_MINUS or keycode == pygame.K_KP_ENTER or keycode == pygame.K_KP_MINUS or keycode == pygame.K_KP_PLUS or keycode == pygame.K_KP_MULTIPLY:
                    localValue = "-"

                if localValue != "" and digitWindowVisible:  # only process keypresses if the digit task is present
                    digitPressTimes.append(time.time())
                    if len(userNumber) < len(goalNumber):
                        if localValue == goalNumber[len(userNumber)]:
                            userNumber = userNumber + localValue

                            newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 1))
                            while newpart == goalNumber[-1]:
                                newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 1))

                            goalNumber = goalNumber + newpart
                            writeDataToFile("keypress", localValue)
                            visitDigits = visitDigits + 1
                            correctDigits = correctDigits + 1
                        else:
                            writeDataToFile("wrongKeypress", localValue)
                            incorrectDigits = incorrectDigits + 1
                            visitIncorrectDigits = visitIncorrectDigits + 1
                    else:
                        writeDataToFile("stringTypedTooLong", localValue)

                    # now update screen
                    # first cover up old message
                    ##blockMaskingOldLocation = pygame.Surface((int(DigitTaskWindowSize[0]-(topLeftCornerOfUserNumber[0]-topLeftCornerOfDigitTaskWindow[0])),100)).convert()
                    ##blockMaskingOldLocation.fill(backgroundColorDigitScreen)
                    ##screen.blit(blockMaskingOldLocation,topLeftCornerOfUserNumber)

                    blockMaskingOldLocation = pygame.Surface((int(
                        DigitTaskWindowSize[0] - (topLeftCornerOfGoalNumber[0] - topLeftCornerOfDigitTaskWindow[0])),
                                                              100)).convert()
                    blockMaskingOldLocation.fill(backgroundColorDigitScreen)
                    screen.blit(blockMaskingOldLocation, topLeftCornerOfGoalNumber)

                    ##color = (0,0,0) #default color: black. Make red if error made
                    ##if (len(userNumber)>0):
                    ##    if (len(userNumber)>len(goalNumber)):
                    ##       color = (255,0,0)
                    ##    elif (goalNumber[0:len(userNumber)] != userNumber):
                    ##        color = (255,0,0)
                    ##
                    ###then post new message
                    ##f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
                    ##UserNumberMessage = f.render(userNumber, True, color)
                    ###blockAtNewLocation = pygame.Surface(UserNumberMessage.get_rect()).convert()
                    ##screen.blit(UserNumberMessage, topLeftCornerOfUserNumber)
                    # screen.blit(blockAtNewLocation,newLocation)

                    ###then post new message
                    f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
                    goalNumberMessage = f.render(goalNumber[len(userNumber):(len(userNumber) + 27)], True,
                                                 (0, 0, 0))
                    screen.blit(goalNumberMessage, topLeftCornerOfGoalNumber)


def updateTrackerScreen(sleepTime):
    print("FUNCTION: " + getFunctionName())
    global screen
    global TrackerTargetCoordinates
    global CursorCoordinates
    global trackerdistanceArray
    global numberCompleted
    global startTime
    global maxTrialTimeDual
    global maxTrialTimeSingleTyping
    global startedClosingThreads
    global cursorMotion
    global trackerWindowVisible

    global stepSizeOfTrackerScreenUpdate

    x = CursorCoordinates[0]
    y = CursorCoordinates[1]

    # always add noise
    # x = x + random.randint(-1,5)
    # y = y + random.randint(-1,5)

    final_x = x
    final_y = y

    # only add noise if tracker is not moving
    motionThreshold = 0.08
    if not (trackerWindowVisible and (
            cursorMotion[0] > motionThreshold or cursorMotion[0] < -1 * motionThreshold or cursorMotion[
        1] > motionThreshold or cursorMotion[1] < -1 * motionThreshold)):
        final_x = x + random.gauss(0, standardDeviationOfNoise)
        final_y = y + random.gauss(0, standardDeviationOfNoise)

    if trackerWindowVisible:  # only add cursormotion if the window is open (i.e., if the participant sees what way cursor moves!)
        final_x = final_x + cursorMotion[0] * scalingCursorMotion
        final_y = final_y + cursorMotion[1] * scalingCursorMotion

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)s
    nrUpdates = int(sleepTime / stepSizeOfTrackerScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if trackerWindowVisible:
        for i in range(0, nrUpdates):

            x = x + delta_x
            y = y + delta_y

            # now check if the cursor is still within screen range
            if (x, y) != CursorCoordinates:
                if x < (topLeftCornerOfTrackingTaskWindow[0] + CursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + CursorSize[0] / 2
                elif x > (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - CursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - CursorSize[0] / 2

                if y < (topLeftCornerOfTrackingTaskWindow[1] + CursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + CursorSize[1] / 2
                elif y > (topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - CursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - CursorSize[1] / 2

                if trackerWindowVisible:  # only update screen when it's visible
                    # now prepare the screen for an update

                    # first do appropriate cover-up
                    oldLocation = ((CursorCoordinates[0] - CursorSize[0] / 2),
                                   (CursorCoordinates[1] - CursorSize[1] / 2))  # gives top-left corner of block
                    blockMaskingOldLocation = pygame.Surface(CursorSize).convert()
                    blockMaskingOldLocation.fill(backgroundColorTrackerScreen)
                    screen.blit(blockMaskingOldLocation, oldLocation)

                    local_distance = math.sqrt((abs(oldLocation[0] - TrackerTargetCoordinates[0])) ** 2 + (
                        abs(oldLocation[1] - TrackerTargetCoordinates[1])) ** 2)

                    if local_distance < (radiusAroundTarget + CursorSize[
                        0] * 2):  # if cursor used to be within radius from target, redraw circle

                        sizeOfLocalScreen = (int(radiusAroundTarget * 2.5), int(radiusAroundTarget * 2.5))
                        localScreen = pygame.Surface(sizeOfLocalScreen).convert()
                        localScreen.fill(backgroundColorTrackerScreen)

                        # draw a filled circle
                        drawowncircle(localScreen, radiusInnerColor,
                                      (int(sizeOfLocalScreen[0] / 2), int(sizeOfLocalScreen[1] / 2)),
                                      radiusAroundTarget,
                                      0)
                        # draw edges think
                        drawowncircle(localScreen, radiusOuterColor,
                                      (int(sizeOfLocalScreen[0] / 2), int(sizeOfLocalScreen[1] / 2)),
                                      radiusAroundTarget,
                                      5)

                        screen.blit(localScreen, ((topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[
                            0] / 2 - sizeOfLocalScreen[0] / 2), (topLeftCornerOfTrackingTaskWindow[1] +
                                                                 TrackingTaskWindowSize[1] / 2 - sizeOfLocalScreen[
                                                                     1] / 2)))  # make area about 30 away from centre

                    # always redraw target
                    newLocation = (x - CursorSize[0] / 2, y - CursorSize[1] / 2)
                    blockAtNewLocation = pygame.Surface(CursorSize).convert()
                    blockAtNewLocation.fill(CursorColor)

                    screen.blit(blockAtNewLocation,
                                newLocation)  # blit puts something new on the screen  (should not contain too much info!!)

            # if cursor used to be within radius from target, redraw cross
            ##                    if (local_distance < (radiusAroundTarget + CursorSize[0]*2)):
            ##                        #add a target cross:
            ##                        crossSurfaceHorizontal = pygame.Surface((TrackerTargetSize[0],4)).convert()
            ##                        crossSurfaceHorizontal.fill(TrackerTargetColor)
            ##                        crossLocation = (TrackerTargetCoordinates[0]-TrackerTargetSize[0]/2,TrackerTargetCoordinates[1]-2)
            ##                        screen.blit(crossSurfaceHorizontal,crossLocation)
            ##
            ##
            ##                        crossSurfaceVertical = pygame.Surface((4,TrackerTargetSize[1])).convert()
            ##                        crossSurfaceVertical.fill(TrackerTargetColor)
            ##                        crossLocation = (TrackerTargetCoordinates[0]-2,TrackerTargetCoordinates[1]-TrackerTargetSize[1]/2)
            ##                        screen.blit(crossSurfaceVertical,crossLocation)

            # always update coordinates
            CursorCoordinates = (x, y)
            pygame.display.flip()
            time.sleep(stepSizeOfTrackerScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % stepSizeOfTrackerScreenUpdate
        if mods != 0:
            time.sleep(mods)
    else:  # if screen is not visible, just update the values
        x = final_x
        y = final_y

        # now check if the cursor is still within screen range
        if (x, y) != CursorCoordinates:
            if x < (topLeftCornerOfTrackingTaskWindow[0] + CursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + CursorSize[0] / 2
            elif x > (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - CursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - CursorSize[0] / 2

            if y < (topLeftCornerOfTrackingTaskWindow[1] + CursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + CursorSize[1] / 2
            elif y > (topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - CursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - CursorSize[1] / 2
        # if display is not updated, sleep for entire time
        time.sleep(sleepTime)

    # always update coordinates
    CursorCoordinates = (x, y)

    writeDataToFile("none", "none")

    # store distance between cursor and target in array of scores

    distance = math.sqrt((abs(CursorCoordinates[0] - TrackerTargetCoordinates[0])) ** 2 + (
        abs(CursorCoordinates[1] - TrackerTargetCoordinates[1])) ** 2)

    # if(distance >= radiusAroundTarget):
    # print("crossed", (time.time()-startTime))

    trackerdistanceArray.append(distance)


def updateDigitScreen():
    print("FUNCTION: " + getFunctionName())
    return


def printTextOverMultipleLines(text, fontsize, color, location):
    print("FUNCTION: " + getFunctionName())
    global screen

    splittedText = text.split("\n")

    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location[0]
    PositionY = location[1]

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        feedbackmessage = f.render(lines, True, color)
        # feedbackrect = feedbackmessage.get_rect()

        # feedbackrect.center = pygame.Rect(PositionX,PositionY,120,120).center      #x-loc, y-loc, xlength,ylength
        screen.blit(feedbackmessage, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def GiveMessageOnScreen(message, timeMessageIsOnScreen):
    print("FUNCTION: " + getFunctionName())
    global screen

    # prepare background
    completebg = pygame.Surface(ExperimentWindowSize).convert()
    completebg.fill(backgroundColorEntireScreen)
    screen.blit(completebg, (0, 0))

    messageAreaObject = pygame.Surface((ExperimentWindowSize[0] - 100, ExperimentWindowSize[1] - 100)).convert()
    messageAreaObject.fill((255, 255, 255))

    topCornerOfMessageArea = (50, 50)
    screen.blit(messageAreaObject, topCornerOfMessageArea)  # make area 50 pixels away from edges

    fontsize = fontsizeGoalAndUserNumber
    color = (0, 0, 0)
    location = (topCornerOfMessageArea[0] + 75, topCornerOfMessageArea[1] + 75)

    printTextOverMultipleLines(message, fontsize, color, location)

    pygame.display.flip()
    time.sleep(timeMessageIsOnScreen)


def GiveCountdownMessageOnScreen(timeMessageIsOnScreen):
    print("FUNCTION: " + getFunctionName())
    global screen

    for i in range(0, timeMessageIsOnScreen):
        # prepare background
        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        messageAreaObject = pygame.Surface(
            (int(ExperimentWindowSize[0] / 5), int(ExperimentWindowSize[1] / 5))).convert()
        messageAreaObject.fill((255, 255, 255))

        topCornerOfMessageArea = (int(ExperimentWindowSize[0] * 2 / 5), int(topLeftCornerOfDigitTaskWindow[1] + 10))
        screen.blit(messageAreaObject, topCornerOfMessageArea)

        message = "Get Ready!\n\n       " + str(timeMessageIsOnScreen - i)

        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 70, topCornerOfMessageArea[1] + 10)

        printTextOverMultipleLines(message, fontsize, color, location)

        pygame.display.flip()
        time.sleep(1)


def ShowStartExperimentScreen():
    print("FUNCTION: " + getFunctionName())
    global mousePressed
    global screen

    mousePressed = False

    # prepare background
    completebg = pygame.Surface(ExperimentWindowSize).convert()
    completebg.fill(backgroundColorEntireScreen)
    screen.blit(completebg, (0, 0))

    messageAreaObject = pygame.Surface((ExperimentWindowSize[0] - 100, ExperimentWindowSize[1] - 100)).convert()
    messageAreaObject.fill((255, 255, 255))

    topCornerOfMessageArea = (50, 50)
    screen.blit(messageAreaObject, topCornerOfMessageArea)  # make area 50 pixels away from edges

    buttonAreaObject = pygame.Surface((ExperimentWindowSize[0] - 300, ExperimentWindowSize[1] - 300)).convert()
    buttonAreaObject.fill((150, 150, 150))
    screen.blit(buttonAreaObject, (150, 150))  # make area 50 pixels away from edges

    fontsize = fontsizeGoalAndUserNumber
    color = (0, 0, 0)
    location = (175, 175)

    message = "Experimenter Please Press Here"
    printTextOverMultipleLines(message, fontsize, color, location)

    pygame.display.flip()

    while not mousePressed:  # wait for a mouseclick
        checkKeyPresses()
        time.sleep(0.25)

    mousePressed = False


def calculatePayrate():
    print("FUNCTION: " + getFunctionName())
    global scoresForPayment
    global baseratePayment
    global maxPayment

    # return scipy.sum(scipy.multiply(scoresForPayment,0.05))
    earnings = baseratePayment + scipy.sum(scoresForPayment)
    print("earnings")
    print(earnings)
    # earnings = earnings * 100 
    # if (earnings < baseratePayment):
    #    earnings = baseratePayment

    return earnings


def reportUserScore():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global startedClosingThreads
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global scoresForPayment
    global scoresOnThisBlock
    global incorrectDigits
    global correctDigits
    global duringTrialScore

    # prepare background
    completebg = pygame.Surface(ExperimentWindowSize).convert()
    completebg.fill(backgroundColorEntireScreen)
    screen.blit(completebg, (0, 0))

    messageAreaObject = pygame.Surface((ExperimentWindowSize[0] - 100, ExperimentWindowSize[1] - 100)).convert()
    messageAreaObject.fill((255, 255, 255))

    topCornerOfMessageArea = (50, 50)
    screen.blit(messageAreaObject, topCornerOfMessageArea)  # make area 50 pixels away from edges

    feedbackText = ""
    scoreForLogging = "none"  # score that's logged

    if partOfExperiment == "dualTask":
        # feedbackText = "Your score: \n"

        # calculate all Values
        ##        trackerScore = scipy.mean(trackerdistanceArray)
        ##
        ##        #round values
        ##        trackerScore = scipy.special.round(trackerScore*10)/10
        ##        maxTrackerDistance = scipy.special.round(maxTrackerDistance*10)/10
        ##
        ##
        ##        digitScore = 0
        ##        if (len(digitPressTimes) < (len(goalNumber) + 1)):     #give a penalty if not all digits have been typed in
        ##            digitScore = maxTrialTimeDual * 1.5
        ##        else:
        ##            digitScore = digitPressTimes[-1] - digitPressTimes[0]
        ##
        ##        #round values
        ##        digitScore = scipy.special.round(digitScore*10)/10

        # maxPossibleDistance = math.sqrt((abs(TrackingTaskWindowSize[0]))**2 + (abs(TrackingTaskWindowSize[1]))**2)  #the maximum distance of tracker target is if the cursor and target align on two corners on a diagonal
        # maxAllowedAverageTrackingDistance = 75
        # maxAllowedTime = maxTrialTime

        ##        #if (focus == "Tracking"):
        ##       score = 100 * (0.45 * (maxPossibleDistance - maxTrackerDistance)/maxPossibleDistance + 0.45 * (maxAllowedAverageTrackingDistance - trackerScore)/maxAllowedAverageTrackingDistance + 0.1 * (maxTrialTime - digitScore)/maxTrialTime)
        ##       score = scipy.special.round(score*100)/100
        ##
        ##        #elif (focus == "Typing"):
        ##        maxAllowedTime = 0.25 * maxTrialTime
        ##        score = 100 * (0.05 * (maxPossibleDistance - maxTrackerDistance)/maxPossibleDistance + 0.05 * (maxAllowedAverageTrackingDistance - trackerScore)/maxAllowedAverageTrackingDistance + 0.9 * (maxTrialTime - digitScore)/maxTrialTime)
        ##        score = scipy.special.round(score*100)/100
        ##
        ##        #else:
        ##        #    print("Wrong focus!!")
        ##
        ##        interkeypressScore = 0
        ##
        ############################################################
        ############################################################
        #        interkeypressScore = 10
        #
        #        if (goalNumber != userNumber):
        #            interkeypressScore = 10
        #        else:   #if too many digits were typed (or errors made), penalized
        #            interkeypressScore = (digitPressTimes[-1] - digitPressTimes[0])/lengthOfGoalNumber

        #        score = 0

        #        maxTrackerDistance = max(trackerdistanceArray)
        #        penaltyA = 0
        #        if (maxTrackerDistance > radiusAroundTarget):   #note: trackerDistanceArray is updated every 20 milliseconds!!
        #            copiedTrackerScores = trackerdistanceArray
        #            copiedTrackerScores.sort()
        #            listOfOutliers = copiedTrackerScores[bisect_right(copiedTrackerScores,radiusAroundTarget):]   #receive a new list of items bigger than a certain value
        #            #penalty = len(listOfOutliers) * -0.0005  #25 samples is 0.5 seconds
        #            #penalty = -0.1*math.exp(min(1000,len(listOfOutliers))/20-3)   #min function is used to prevent number overflow
        #            #penalty = max(-0.25,penalty)
        #            #penaltyA = -0.1*math.exp(min(1000,len(listOfOutliers))/36.067-0.6931472)  #min function is used to prevent number overflow;
        #                                                                                    #function passes -0.1 at t=.5 sec and -0.2 at t=1 sec
        #            #penaltyA = -0.1*math.exp(min(1000,len(listOfOutliers))/36.067-1.5)+0.02294  #min function is used to prevent number overflow;
        #                                                                                    #less steep penalty function than previous one used
        #
        #            penaltyA = -0.1*math.exp(min(1000,len(listOfOutliers))/18.033688-0.6931472)  #min function is used to prevent number overflow;
        #                                                                                    #function passes -0.1 at t=.25 sec and -0.2 at t=0.5 sec
        #            #print(penalty)
        #
        #            #penalty: at 0.5 sec -1.5 cent, at 1 sec -6 cents, at 1.2 sec -10 cents, at (about) 1.5 sec -20 cents
        #            #penalty = -10
        #
        #
        #        penaltyB = 0
        #        if (len(digitPressTimes)>(lengthOfGoalNumber + 1)):
        #            penaltyB = (len(digitPressTimes) - (lengthOfGoalNumber + 1))*-0.01  #lose 1 cent for every incorrect keypress
        #
        #
        #        #score = scipy.special.round((0.15* math.exp(-4.6209812*interkeypressScore + 1.1552453) + penaltyA + penaltyB) *1000)/1000
        #       score = scipy.special.round((0.15* math.exp(-0.0854888*interkeypressScore + 0.0170978) + penaltyA + penaltyB) *1000)/1000

        ################################################################
        ################################################################

        # print(str(penaltyB) + " " + str(len(digitPressTimes)) + " "  + str(lengthOfGoalNumber + 1))

        # =15*EXP(-0.0854888*(A27/20)+0.0170978)

        # if (score < -0.20):

        # maxTrackerDistance = max(trackerdistanceArray)

        # if (maxTrackerDistance > radiusAroundTarget): 
        #   score = 0
        # else:
        #    gain = correctDigits * 0.1 
        #    digitPenalty = incorrectDigits * -0.01 
        #    score = gain + digitPenalty 
        #    print "correct digits:"
        #    print correctDigits
        #    print "incorrect digits:"
        #    print incorrectDigits
        #    print "gain:"
        #    print gain

        score = duringTrialScore  # use score generated by updateIntermediateScore()

        feedbackScore = score
        # feedbackText = feedbackText + "\n\n" + str(score) + "\n\n" + str(trackerScore) + "  pixels \n\n" + str(maxTrackerDistance) + "  pixels" + "\n\n" +str(digitScore) + "  seconds"
        if score > 0:
            feedbackText = "+" + str(feedbackScore) + " points"
        else:
            feedbackText = str(feedbackScore) + " points"

        scoresForPayment.append(score)
        scoresOnThisBlock.append(score)  # store score, so average performance can be reported
        scoreForLogging = score

    elif partOfExperiment == "singleTaskTracking":
        feedbackText = "Your maximum distance: \n"
        if trackingTaskPresent:
            maxTrackerDistance = max(trackerdistanceArray)
            # round values
            maxTrackerDistance = scipy.special.round(maxTrackerDistance * 10) / 10

            feedbackText = feedbackText + "\n\n" + str(maxTrackerDistance) + "  pixels"

            scoresOnThisBlock.append(maxTrackerDistance)

            scoreForLogging = maxTrackerDistance

    elif partOfExperiment == "singleTaskTyping":
        feedbackText = "You made: \n"
        if digitTaskPresent:
            #    digitScore = maxTrialTimeSingleTyping * 1.5
            # else:
            digitScore = digitPressTimes[-1] - digitPressTimes[0]
            digitErrors = incorrectDigits
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText = feedbackText + "\n\n" + str(digitErrors) + "  errors"

            # scoresOnThisBlock.append(digitScore)
            scoresOnThisBlock.append(
                digitErrors)
            scoreForLogging = digitScore

    if feedbackText != "":
        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)

        printTextOverMultipleLines(feedbackText, fontsize, color, location)

    pygame.display.flip()
    writeDataToFile("scoreGiven", str(scoreForLogging))
    time.sleep(timeFeedbackIsGiven)

    if len(scoresOnThisBlock) % 5 == 0:  # every fifth trial, report mean score
        # prepare background
        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))
        messageAreaObject = pygame.Surface((ExperimentWindowSize[0] - 100, ExperimentWindowSize[1] - 100)).convert()
        messageAreaObject.fill((255, 255, 255))
        topCornerOfMessageArea = (50, 50)
        screen.blit(messageAreaObject, topCornerOfMessageArea)  # make area 50 pixels away from edges

        feedbackText2 = "Your average performance over the last five trials:\n\n"
        meanscore = scipy.special.round(scipy.mean(
            scoresOnThisBlock[-2:]) * 100) / 100  # report meanscore 
        feedbackText2 = feedbackText2 + str(meanscore)
        if partOfExperiment == "singleTaskTracking":
            feedbackText2 = feedbackText2 + " pixels"
        elif partOfExperiment == "singleTaskTyping":
            feedbackText2 = feedbackText2 + " errors"
        elif partOfExperiment == "dualTask":
            feedbackText2 = "Block " + str(int(len(
                scoresOnThisBlock) / 5)) + " of 8 complete. Your average performance over the last five trials:\n\n" + str(
                meanscore) + " points"

        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)

        printTextOverMultipleLines(feedbackText2, fontsize, color, location)
        pygame.display.flip()
        writeDataToFile("avscoreGiven", str(meanscore))
        time.sleep(20)


def generateGoalNumber():
    print("FUNCTION: " + getFunctionName())
    global goalNumber
    global lengthOfGoalNumber

    if lengthOfGoalNumber == 240:
        goalNumber = ''.join(random.sample(numbersAvailableForGoalNumber, lengthOfGoalNumber))
    elif lengthOfGoalNumber < 19:
        goalNumber = ''.join(random.sample(numbersAvailableForGoalNumber, 9))
        newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 9))
        # prevent situations with repeating digits
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        newpart = newpart[0:(lengthOfGoalNumber - 9)]
        goalNumber = goalNumber + newpart

    elif lengthOfGoalNumber == 27:  ### changed tp == 27
        goalNumber = ''.join(random.sample(numbersAvailableForGoalNumber, 9))
        newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 9))
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]

        goalNumber = goalNumber + newpart

        newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 9))
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]
        if newpart[0] == goalNumber[-1]:
            newpart = newpart[1:] + goalNumber[-1]

        newpart = newpart[0:(lengthOfGoalNumber - 18)]
        goalNumber = goalNumber + newpart


def runSingleTaskTypingTrials(booleanThisIsAPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeSingleTyping
    global numberCompleted
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global userNumber
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global digitWindowVisible
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global scoresOnThisBlock
    global incorrectDigits
    global correctDigits

    blockNumber = blockNumber + 1
    scoresOnThisBlock = []
    numberOfTrials = numberOfSingleTaskTypingTrials

    if booleanThisIsAPracticeTrial:
        partOfExperiment = "practiceTyping"
        GiveMessageOnScreen("Typing only\n\nIn these trials you only perform the typing task.\nType in the digits that "
                            "are shown on the screen as fast as possible.\n\nIf you make a mistake, the string of digits "
                            "won't progress \n(In future trials, you would also lose points)", 15)
        numberOfTrials = 2
    else:
        partOfExperiment = "singleTaskTyping"

        GiveMessageOnScreen("Typing only\n\nType as fast as possible", 5)

    for i in range(0, numberOfTrials):
        incorrectDigits = 0
        correctDigits = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  ###clear all events
        trackerWindowVisible = False
        digitWindowVisible = True

        trackingTaskPresent = False
        digitTaskPresent = True
        trialNumber = trialNumber + 1
        trackingWindowVisitCounter = 0
        digitWindowVisitCounter = 0

        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        startTime = time.time()

        if digitTaskPresent:
            generateGoalNumber()
            numberCompleted = False
            userNumber = ""
            digitPressTimes = [startTime]

            if digitWindowVisible:
                openDigitWindow()
            else:
                closeDigitWindow()

        writeDataToFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (not numberCompleted) and ((time.time() - startTime) < maxTrialTimeSingleTyping) and EnvironmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates

            pygame.display.flip()
            time.sleep(0.02)

        if (time.time() - startTime) >= maxTrialTimeSingleTyping:
            writeDataToFile("trialStopTooMuchTime", "none")
        elif not EnvironmentIsRunning:
            writeDataToFile("trialStopEnvironmentStopped", "none")
        else:
            writeDataToFile("trialStop", "none")

        if not booleanThisIsAPracticeTrial:
            # now give feedback
            reportUserScore()


def runSingleTaskTrackingTrials(booleanThisIsAPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeSingleTracking
    global numberCompleted
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global TrackerTargetCoordinates
    global CursorCoordinates
    global startedClosingThreads
    global trackingTaskPresent
    global digitTaskPresent
    global joystickObject
    global cursorMotion
    global partOfExperiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global digitWindowVisible
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global scoresOnThisBlock

    blockNumber = blockNumber + 1
    scoresOnThisBlock = []

    numberOfTrials = numberOfSingleTaskTrackingTrials

    if booleanThisIsAPracticeTrial:
        partOfExperiment = "practiceTracking"
        GiveMessageOnScreen(
            "Tracking only\n\nIn these trials you only perform the tracking task.\nYou can test how the joystick works, and see how the cursor moves around.\nThe cursor moves around freely untill you move it.",
            15)
        numberOfTrials = 2
    else:
        partOfExperiment = "singleTaskTracking"

        GiveMessageOnScreen(
            "Tracking only\n\nUse these trials to estimate the speed of the cursor, \nbut keep the cursor inside the shield",
            5)

    for i in range(0, numberOfTrials):

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  ###clear all events
        trackerWindowVisible = True
        digitWindowVisible = False

        trackingTaskPresent = True
        digitTaskPresent = False

        trialNumber = trialNumber + 1
        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        startTime = time.time()

        trackingWindowVisitCounter = 0
        digitWindowVisitCounter = 0

        if trackingTaskPresent:
            cursorMotion = (0, 0)
            pygame.joystick.init()
            joystickObject = pygame.joystick.Joystick(0)
            joystickObject.init()

            # initially, cursor starts at same location as target
            CursorCoordinates = TrackerTargetCoordinates

            if trackerWindowVisible:
                openTrackerWindow()
            else:
                closeTrackerWindow()

            trackerdistanceArray = []

        writeDataToFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while ((time.time() - startTime) < maxTrialTimeSingleTracking) and EnvironmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates

            if trackingTaskPresent:
                updateTrackerScreen(0.02)

            pygame.display.flip()
            # time.sleep(0.02)

        if not EnvironmentIsRunning:
            writeDataToFile("trialStopEnvironmentStopped", "none")
        else:
            writeDataToFile("trialStop", "none")

        # now give feedback
        # reportUserScore()


def drawowncircle(image, colour, origin, radius, width=0):
    print("FUNCTION: " + getFunctionName())
    # based on recommendation on pygame website
    if width == 0:
        pygame.draw.circle(image, colour, origin, int(radius))
    else:
        if radius > 65534 / 5: radius = 65534 / 5
        circle = pygame.Surface([radius * 2 + width, radius * 2 + width]).convert_alpha()
        circle.fill([0, 0, 0, 0])
        pygame.draw.circle(circle, colour, (int(circle.get_width() / 2), int(circle.get_height() / 2)),
                           int(radius + (width / 2)))
        if int(radius - (width / 2)) > 0: pygame.draw.circle(circle, [0, 0, 0, 0], (
            int(circle.get_width() / 2), int(circle.get_height() / 2)), abs(int(radius - (width / 2))))
        image.blit(circle, [origin[0] - (circle.get_width() / 2), origin[1] - (circle.get_height() / 2)])


def closeDigitWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global digitWindowVisible
    global radiusAroundTarget
    global trackerdistanceArray
    global outsideRadius

    # draw background

    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(coverUpColor)

    screen.blit(bg, topLeftCornerOfDigitTaskWindow)  # make area about 30 away from centre
    digitWindowVisible = False


def openDigitWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global digitWindowVisible
    global digitWindowVisitCounter
    global outsideRadius
    global visitDigits
    global visitIncorrectDigits
    global trackerdistanceArray
    global visitStartTime

    visitStartTime = time.time()
    print("start time:")
    print(visitStartTime)

    trackerdistanceArray = []
    outsideRadius = False
    visitDigits = 0
    visitIncorrectDigits = 0

    digitWindowVisitCounter = digitWindowVisitCounter + 1

    # draw background
    bg = pygame.Surface(DigitTaskWindowSize).convert()
    bg.fill((255, 255, 255))
    screen.blit(bg, topLeftCornerOfDigitTaskWindow)  # make area about 30 away from centre

    ##    #then post new message
    ##    f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
    ##    GoalNumberMessage = f.render(goalNumber, True, (0, 0, 0))
    ##    #blockAtNewLocation = pygame.Surface(UserNumberMessage.get_rect()).convert()
    ##    screen.blit(GoalNumberMessage, topLeftCornerOfGoalNumber)
    ##
    ##    color = (0,0,0) #default color: black. Make red if error made
    ##    if (len(userNumber)>0):
    ##        if (len(userNumber)>len(goalNumber)):
    ##            color = (255,0,0)
    ##        elif (goalNumber[0:len(userNumber)] != userNumber):
    ##            color = (255,0,0)
    ##
    ##    f2 = pygame.font.Font(None, fontsizeGoalAndUserNumber)
    ##    UserNumberMessage = f2.render(userNumber, True, color)
    ##    screen.blit(UserNumberMessage, topLeftCornerOfUserNumber)

    f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
    goalNumberMessage = f.render(goalNumber[len(userNumber):(len(userNumber) + 27)], True,
                                 (0, 0, 0))
    screen.blit(goalNumberMessage, topLeftCornerOfGoalNumber)
    digitWindowVisible = True


def closeTrackerWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackerWindowVisible

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(coverUpColor)
    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre
    trackerWindowVisible = False


def switchWindows(message):
    print("FUNCTION: " + getFunctionName())
    global trackerWindowVisible
    global digitWindowVisible

    if message == "openTracking" and (
            partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask"):  # switching is only done in dual-task
        if trackingTaskPresent:
            openTrackerWindow()

        if digitWindowVisible and digitTaskPresent:
            closeDigitWindow()

    elif message == "closeTracking" and (
            partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask"):  # switching is only done in dual-task
        if trackingTaskPresent:
            closeTrackerWindow()

        if (not digitWindowVisible) and digitTaskPresent:
            openDigitWindow()


def openTrackerWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackerWindowVisible
    global trackingWindowVisitCounter
    global cursorMotion
    global visitScore
    global visitEndTime
    global CursorColor

    visitEndTime = time.time()
    print("End Time:")
    print(visitEndTime)

    if partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask":
        updateIntermediateScore()

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(backgroundColorTrackerScreen)

    trackingWindowVisitCounter = trackingWindowVisitCounter + 1

    # draw a filled circle
    drawowncircle(bg, radiusInnerColor,
                  (int(TrackingTaskWindowSize[0] / 2), int(TrackingTaskWindowSize[1] / 2)),
                  radiusAroundTarget, 0)

    # draw edges think
    drawowncircle(bg, radiusOuterColor,
                  (int(TrackingTaskWindowSize[0] / 2), int(TrackingTaskWindowSize[1] / 2)),
                  radiusAroundTarget, 5)

    # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size. The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.

    # screen.blit(circle)

    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre

    newLocation = (CursorCoordinates[0] - (CursorSize[0] / 2), CursorCoordinates[1] - (CursorSize[1] / 2))
    blockAtNewLocation = pygame.Surface(CursorSize).convert()
    blockAtNewLocation.fill(CursorColor)
    screen.blit(blockAtNewLocation, newLocation)  # blit puts something new on the screen  (should not contain too much info!!)

    ##    #add a target cross:
    ##    crossSurfaceHorizontal = pygame.Surface((TrackerTargetSize[0],4)).convert()
    ##    crossSurfaceHorizontal.fill(TrackerTargetColor)
    ##    crossLocation = (TrackerTargetCoordinates[0]-TrackerTargetSize[0]/2,TrackerTargetCoordinates[1]-2)
    ##    screen.blit(crossSurfaceHorizontal,crossLocation)
    ##
    ##
    ##    crossSurfaceVertical = pygame.Surface((4,TrackerTargetSize[1])).convert()
    ##    crossSurfaceVertical.fill(TrackerTargetColor)
    ##    crossLocation = (TrackerTargetCoordinates[0]-2,TrackerTargetCoordinates[1]-TrackerTargetSize[1]/2)
    ##    screen.blit(crossSurfaceVertical,crossLocation)

    trackerWindowVisible = True

    # get the cursor angle
    measuredMotion = (joystickObject.get_axis(0), joystickObject.get_axis(1))
    cursorMotion = (measuredMotion[0], measuredMotion[1])
    # print("motion " + str(cursorMotion[0]) +  " " + str(cursorMotion[1]))

    if partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask":
        intermediateMessage = str(visitScore) + " Points"

        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (900, 65)

        printTextOverMultipleLines(intermediateMessage, fontsize, color, location)


def updateIntermediateScore():
    print("FUNCTION: " + getFunctionName())
    global duringTrialScore  # cumulative score for the current trial
    global outsideRadius  # boolean - did the cursor leave the circle
    global visitDigits  # number of correctly typed digits
    global visitIncorrectDigits  # number of incorrectly typed digits
    global intermediateScoreVisit  # counts the number of times this function is called (for error checking)
    global trackerdistanceArray
    global radiusAroundTarget
    global visitScore  # Score for one visit to the digit window
    global visitTime
    global visitStartTime
    global visitEndTime
    global CursorColor
    global writeMaxDistance
    global writeMeanDistance
    global writeEndDistance
    global writeStartDistance
    global penalty

    intMaxTrackerDistance = max(trackerdistanceArray)
    if intMaxTrackerDistance > radiusAroundTarget:
        # print "Left Target"
        outsideRadius = True

        ###code for changing cursor color
        CursorColor = (255, 0, 0)  # red
    else:
        CursorColor = (0, 0, 255)  # blue

    writeMaxDistance = max(trackerdistanceArray)
    writeMeanDistance = (sum(trackerdistanceArray) / len(trackerdistanceArray))
    writeEndDistance = trackerdistanceArray[-1]
    writeStartDistance = trackerdistanceArray[0]

    trackerdistanceArray = []

    intermediateScoreVisit = intermediateScoreVisit + 1

    if outsideRadius:

        if penalty == "lose500":
            # loose 500
            visitScore = (((visitDigits + 10) + (visitIncorrectDigits - 5)) - 500)

        if penalty == "loseAll":
            # loose all
            visitScore = 0 * ((visitDigits + 10) + (visitIncorrectDigits - 5))

        if penalty == "loseHalf":
            # loose half
            visitScore = 0.5 * ((visitDigits * 10) + (visitIncorrectDigits * -5))  # penalty for exit is to lose half points
    else:
        visitScore = (visitDigits * 10) + (visitIncorrectDigits * -5)  # gain is 10 for correct digit and -5 for incorrect digit

    # add the score for this digit task visit to the overall trial score
    # duringtrial score is used in reportUserScore
    duringTrialScore = duringTrialScore + visitScore

    # print "Running of function:"
    # print intermediateScoreVisit
    # print "Visit Score:"
    # print visitScore
    # print "Cumulative Trial Score:"
    # print duringTrialScore

    visitTime = visitEndTime - visitStartTime
    print(visitTime)
    writeSummaryDataToFile()
    outsideRadius = False


def runDualTaskTrials(booleanThisIsAPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeDual
    global numberCompleted
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global userNumber
    global TrackerTargetCoordinates
    global CursorCoordinates
    global startedClosingThreads
    global trackingTaskPresent
    global digitTaskPresent
    global joystickObject
    global cursorMotion
    global partOfExperiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global digitWindowVisible
    global numbersAvailableForGoalNumber
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global scoresOnThisBlock
    global incorrectDigits
    global correctDigits
    global duringTrialScore
    global outsideRadius
    global visitDigits
    global visitIncorrectDigits
    global intermediateScoreVisit
    global visitStartTime
    global visitEndTime

    blockNumber = blockNumber + 1
    scoresOnThisBlock = []

    numberOfTrials = numberOfDualTaskTrials

    if booleanThisIsAPracticeTrial:
        maxTrialTimeDual = 30
        partOfExperiment = "practiceDualTask"
        GiveMessageOnScreen(
            "Tracking + Typing\n\nYou will now practice performing both tasks at the same time.\nBy default you will start with viewing the typing task.\nPress the trigger on the joystick to control the tracking task.\nRelease the trigger to control the typing task.\nYou can only perform one task at a time.",
            15)
        GiveMessageOnScreen(
            "Your objective is to:\nType the number in as fast as possible (in future trials: this way you gain points),\nbut keep the cursor inside the shield (or else, you lose points)\nTyping errors also make you lose points",
            10)
        numberOfTrials = 2
    else:
        maxTrialTimeDual = 30
        partOfExperiment = "dualTask"
        GiveMessageOnScreen(
            "Tracking + Typing\n\nType the number in as fast as possible (this way you gain points),\nbut keep the cursor inside the shield (or else, you lose points).\nTyping errors also make you lose points\n\nImportant: Your performance on these trials will add to your score.",
            18)
        GiveMessageOnScreen(
            "The cursor will move at the same speed as before.\nThe shield is the same size\n\nTo open the tracker window, keep the trigger pressed.\nTo open the digit window, release the trigger.\nYou can only work on one task at a time",
            15)

    for i in range(0, numberOfTrials):

        duringTrialScore = 0
        intermediateScoreVisit = 0
        outsideRadius = False
        visitDigits = 0
        visitIncorrectDigits = 0

        # incorrectDigits = 0 # reset digit counters so that only counter for dualtask is passed to reportuserscore
        # correctDigits = 0 # ditto

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  ###clear all events

        trackerWindowVisible = False
        digitWindowVisible = True
        trackingTaskPresent = True
        digitTaskPresent = True

        trackingWindowVisitCounter = 0
        digitWindowVisitCounter = 0

        trialNumber = trialNumber + 1

        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        startTime = time.time()

        if trackingTaskPresent:
            cursorMotion = (0, 0)
            pygame.joystick.init()
            joystickObject = pygame.joystick.Joystick(0)
            joystickObject.init()

            # initially, cursor starts at same location as target
            CursorCoordinates = TrackerTargetCoordinates

            if trackerWindowVisible:
                openTrackerWindow()
            else:
                closeTrackerWindow()

            trackerdistanceArray = []

        if digitTaskPresent:
            generateGoalNumber()
            numberCompleted = False
            userNumber = ""
            digitPressTimes = [startTime]

            if digitWindowVisible:
                openDigitWindow()
            else:
                closeDigitWindow()

        writeDataToFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (not numberCompleted) and ((time.time() - startTime) < maxTrialTimeDual) and EnvironmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates

            if trackingTaskPresent:
                updateTrackerScreen(0.02)

            pygame.display.flip()
            # time.sleep(0.02)

        visitEndTime = time.time()
        updateIntermediateScore()

        if (time.time() - startTime) >= maxTrialTimeDual:
            writeDataToFile("trialStopTooMuchTime", "none")
        elif not EnvironmentIsRunning:
            writeDataToFile("trialStopEnvironmentStopped", "none")
        else:
            writeDataToFile("trialStop", "none")

        if not booleanThisIsAPracticeTrial:
            # now give feedback
            reportUserScore()


def readInputAndCreateOutputFiles():
    print("FUNCTION: " + getFunctionName())
    """
    Read the participant file / set the participant condition.
    Initialize the output files
    """
    global subjNr
    global conditions
    global outputFile
    global summaryOutputFile
    global firstTrial

    subjNrStr = input("Please enter the subject number here: ")
    subjNr = int(subjNrStr)

    f = open('participantConditions.csv','r')
    individualLines = f.read().split('\n') ## read by lines
    lines = list(map(lambda x: x.split(';'), individualLines) )     #split all elements
    subjectLine = []
    for line in lines:
        if line[0] == subjNrStr:
            subjectLine = line[1:]
    if not subjectLine:
        raise Exception("Invalid subject number")

    conditions = subjectLine
    print(conditions)
    f.close()

    firstTrial = input("First trial? (yes/no) ")

    ##enter 'yes' if first 'no' if not

    fileName = "participant" + subjNrStr + "data.csv"

    if not os.path.exists(fileName):
        outputFile = open(fileName, 'w')  # contains the user data
    else:
        fileName = "participant" + subjNrStr + "_" + str(random.randint(100000000, 999999999)) + "data.csv"
        outputFile = open(fileName, 'w')  # contains the user data

    outputText = "SubjectNr;CurrentTime;LocalTime;BlockNumber;TrialNumber;partOfExperiment;TrackingTaskPresent;DigitTaskPresent;TrackerWindowVisible;DigitWindowVisible;TrackingWindowVisitCounter;DigitWindowVisitCounter;RadiusAroundTarget;standardDeviationOfNoise;CursorDistanceX;CursorDistanceY;CursorDistanceDirect;CursorCoordinatesX;CursorCoordinatesY;TrackerTargetCoordinatesX;TrackerTargetCoordinatesY;cursorMotionX;cursorMotionY;userNumber;goalNumber;numberCompleted;LengthOfUserNumber;LengthofGoalNumber;Eventmessage1;Eventmessage2" + "\n"
    outputFile.write(outputText)

    ########################Second Output File######################################

    print("Summary file line 0")

    summaryFileName = "participant" + subjNrStr + "SummaryData.csv"

    if not os.path.exists(summaryFileName):
        summaryOutputFile = open(summaryFileName, 'w')  # contains the user data
    else:
        summaryFileName = "participant" + subjNrStr + "_" + str(random.randint(100000000, 999999999)) + "SummaryData.csv"
        summaryOutputFile = open(summaryFileName, 'w')  # contains the user data

    summaryOutputText = "SubjectNr;BlockNumber;TrialNumber;partOfExperiment;standardDeviationOfNoise;visitTime;visitCorrectDigits;visitIncorrectDigits;visitScore;outsideRadius;maxDistance;meanDistance;endDistance;startDistance;" + "\n"

    print("Summary file line 3")
    print(summaryOutputText)

    summaryOutputFile.write(summaryOutputText)

    print("Summary file line 4")
    print(summaryFileName)


def main():
    print("FUNCTION: " + getFunctionName())
    global screen
    global numberCompleted
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global userNumber
    global TrackerTargetCoordinates
    global CursorCoordinates
    global startedClosingThreads
    global trackingTaskPresent
    global digitTaskPresent
    global joystickObject
    global cursorMotion
    global partOfExperiment
    global EnvironmentIsRunning  # variable that states that there is a main window
    global conditions
    global radiusAroundTarget
    global numbersAvailableForGoalNumber
    global scoresForPayment
    global scoresOnThisBlock
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment
    global baseratePayment
    global firstTrial
    global penalty
    global currentCondition

    readInputAndCreateOutputFiles()

    scoresForPayment = []
    scoresOnThisBlock = []

    timeOfCompleteStartOfExperiment = time.time()

    pygame.init()
    screen = pygame.display.set_mode(ExperimentWindowSize, pygame.FULLSCREEN)
    pygame.display.set_caption("Multitasking 2.0")
    EnvironmentIsRunning = True

    ShowStartExperimentScreen()

    if firstTrial == "yes":
        GiveMessageOnScreen(
            "Welcome to the tracking + typing experiment!\n\n\nYou will first start practicing the three types of trials.", 10)

    numbersAvailableForGoalNumber = "123123123"

    if firstTrial == "yes":
        # do practice trials
        runSingleTaskTrackingTrials(True)
        runSingleTaskTypingTrials(True)
        runDualTaskTrials(True)
        GiveMessageOnScreen("Now we will test your performance on these tasks. Try to earn as many points as possible", 10)

    for pos in range(0, len(conditions)):
        currentCondition = conditions[pos]

        if len(currentCondition) != 4:
            raise Exception("Current Condition" + currentCondition + " has invalid length " + len(currentCondition))

        # noise values are h (high), m (medium) or l (low)
        if currentCondition[0] == "h":
            standardDeviationOfNoise = 5
            noiseMsg = "hoher"
        elif currentCondition[0] == "m":
            standardDeviationOfNoise = 5
            noiseMsg = "mittlerer"
        elif currentCondition[0] == "l":
            standardDeviationOfNoise = 3
            noiseMsg = "niedriger"
        else:
            raise Exception("Invalid noise " + currentCondition[0])

        # radius is S (small) or B (big)
        if currentCondition[1] == "S":  # small radius
            radiusAroundTarget = 80
        elif currentCondition[1] == "B":
            radiusAroundTarget = 120
        else:
            raise Exception("Invalid radius " + currentCondition[1])

        # set of digits is 1-9 (9) or 1-3 (3)
        if currentCondition[2] == "9":
            numbersAvailableForGoalNumber = "123456789"
        elif currentCondition[2] == "3":
            numbersAvailableForGoalNumber = "123123123"
        else:
            raise Exception("Invalid number " + currentCondition[2])

        # define penalty
        if currentCondition[3] == "a":
            penalty = "loseAll"
            penaltyMsg = "alle"
        elif currentCondition[3] == "h":
            penalty = "loseHalf"
            penaltyMsg = "die Hälfte deiner"
        elif currentCondition[3] == "n":
            penalty = "lose500"
            penaltyMsg = "500"
        else:
            raise Exception("Invalid penalty " + currentCondition[3])

        # message = "NEW BLOCK\n\n\n\nDuring the upcoming trials:\n\n\nYour cursor drifts at " + messageNoise + " speed"
        # GiveMessageOnScreen(message, 10)

        message = "Neuer Block: der Cursor bewegt sich mit " + noiseMsg + " Geschwindigkeit. Für jede korrekt " \
                  "eingegebene Ziffer bekommst du 10 Punkte. Bei jeder falsch eingetippten Ziffer gibt es 5 Punkte " \
                  "Abzug. Wenn der Cursor den Kreis verlässt, verlierst du " + penaltyMsg + " deiner Punkte."
        GiveMessageOnScreen(message, 10)

        runSingleTaskTrackingTrials(False)
        runSingleTaskTypingTrials(False)
        runDualTaskTrials(False)

        message = "So far, you've scored: " + str(calculatePayrate() - baseratePayment) + " points"
        GiveMessageOnScreen(message, 8)

        # if (pos != (len(conditions)-1)):
        #    if (pos%2 == 0):
        #        GiveMessageOnScreen("You now have a short break of 30 seconds.\nPlease stay seated",20)
        #        GiveMessageOnScreen("10 seconds left",10)
        #    else:
        #        GiveMessageOnScreen("You now have a short break of 30 seconds.\nPlease stay seated",20) 

        #        GiveMessageOnScreen("10 seconds left",10)

    GiveMessageOnScreen("This is the end of the task.", 5)

    payment = calculatePayrate()
    print(payment)

    quit_app()


def quit_app():
    print("FUNCTION: " + getFunctionName())
    global EnvironmentIsRunning
    global outputFile
    global summaryOutputFile

    EnvironmentIsRunning = False

    pygame.display.quit()
    pygame.quit()

    outputFile.close()
    summaryOutputFile.close()


def getFunctionName():
    return inspect.stack()[1][3]


if __name__ == '__main__':
    main()
