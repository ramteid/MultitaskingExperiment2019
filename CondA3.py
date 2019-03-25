# coding=utf-8
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
import random
import time
import traceback

import pygame
import scipy
import scipy.special
import datetime

######initialize global variables

incorrectDigits = 0
duringTrialScore = 0
outsideRadius = False
visitDigits = 0
visitIncorrectDigitsNum = 0
visitScore = 0
visitEndTime = 0
visitStartTime = 0

global penalty
penalty = ""

timeFeedbackIsGiven = 4

global environmentIsRunning  # True if there is a display
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
timeFeedbackIsShown = 4
backgroundColorTrackerScreen = (255, 255, 255)  # white
backgroundColorDigitScreen = backgroundColorTrackerScreen
backgroundColorEntireScreen = (50, 50, 50)  # gray
coverUpColor = (200, 200, 200)  # very light gray
TrackerTargetColor = (0, 0, 0)  # black
radiusInnerColor = (255, 204, 102)  # orange
radiusOuterColor = (255, 0, 0)  # red
CursorColor = (0, 0, 255)  # blue

ExperimentWindowSize = (1280, 1024)  # eye-tracker screen: 1280*1024 pixels
TrackingTaskWindowSize = digitTaskWindowSize = (450, 450)
TrackerTargetSize = CursorSize = (20, 20)

topLeftCornerOfDigitTaskWindow = (int(ExperimentWindowSize[0] - TrackingTaskWindowSize[0] - digitTaskWindowSize[0]) / 3, 50)
topLeftCornerOfTrackingTaskWindow = (2 * topLeftCornerOfDigitTaskWindow[0] + digitTaskWindowSize[0], 50)

topLeftCornerOfGoalNumber = (digitTaskWindowSize[0] / 2 - 150 + topLeftCornerOfDigitTaskWindow[0],
                             digitTaskWindowSize[1] / 2 - 20 + topLeftCornerOfDigitTaskWindow[1])
topLeftCornerOfUserNumber = (digitTaskWindowSize[0] / 2 - 150 + topLeftCornerOfDigitTaskWindow[0],
                             digitTaskWindowSize[1] / 2 + 20 + topLeftCornerOfDigitTaskWindow[1])
numberCompleted = False  # boolean: did user completely type in the number?
goalNumber = "123456789"
enteredDigitsStr = ""
lengthOfGoalNumber = 27

numbersAvailableForGoalNumber = "123456789"
TrackerTargetCoordinates = (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] / 2,
                            topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] / 2)
CursorCoordinates = (TrackingTaskWindowSize[0] / 2 - (CursorSize[0] / 2), TrackingTaskWindowSize[1] / 2 - (CursorSize[0] / 2))

fontsizeGoalAndUserNumber = 30

maxTrialTimeDual = 120  # maximum time for dual-task trials 
maxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
maxTrialTimeSingleTyping = 20  # maximum time for single-task typing

numberOfDualTaskTrials = 3
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


def writeSummaryDataFile(visitTime, outsideRadius1, writeMaxDistance, writeMeanDistance, writeEndDistance, writeStartDistance):
    print("FUNCTION: " + getFunctionName())
    global summaryOutputFile
    global subjNr
    global partOfExperiment
    global blockNumber
    global trialNumber
    global standardDeviationOfNoise
    global visitScore
    global visitDigits
    global visitIncorrectDigitsNum

    summaryOutputText = \
        str(subjNr) + ";" + \
        str(blockNumber) + ";" + \
        str(trialNumber) + ";" + \
        partOfExperiment + ";" + \
        str(standardDeviationOfNoise) + ";" + \
        str(visitTime) + ";" + \
        str(visitDigits) + ";" + \
        str(visitIncorrectDigitsNum) + ";" + \
        str(visitScore) + ";" + \
        str(outsideRadius1) + ";" + \
        str(writeMaxDistance) + ";" + \
        str(writeMeanDistance) + ";" + \
        str(writeEndDistance) + ";" + \
        str(writeStartDistance) + "\n"

    summaryOutputFile.write(summaryOutputText)


def writeParticipantDataFile(Eventmessage1, message2):
    global outputFile
    global subjNr
    global numberCompleted
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global enteredDigitsStr
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

    outputuserNumber = enteredDigitsStr
    outputgoalNumber = goalNumber

    currentTime = time.time() - timeOfCompleteStartOfExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracker)
    currentTime = scipy.special.round(currentTime * 10000) / 10000

    trialTime = time.time() - startTime  # this is a local time (reset at the start of each trial)
    trialTime = scipy.special.round(trialTime * 10000) / 10000

    if not trackingTaskPresent:
        outputCursorCoordinates = (-987654321, -987654321)  # keep it in number format to make later analysis easier :-)
        outputTrackerTargetCoordinates = (-987654321, -987654321)
        outputcursorMotion = (-987654321, -987654321)
        outputCursorDistance = (-987654321, -987654321, -987654321)  # (horiz, vert, straight line)
    else:
        outputCursorCoordinates = (scipy.special.round(CursorCoordinates[0] * 100) / 100,
                                   scipy.special.round(CursorCoordinates[1] * 100) / 100)
        outputTrackerTargetCoordinates = (scipy.special.round(TrackerTargetCoordinates[0] * 100) / 100,
                                          scipy.special.round(TrackerTargetCoordinates[1] * 100) / 100)

        outputcursorMotion = (
            scipy.special.round(cursorMotion[0] * 1000) / 1000, scipy.special.round(cursorMotion[1] * 1000) / 1000)

        distanceXY = (abs(TrackerTargetCoordinates[0] - CursorCoordinates[0]),
                      abs(TrackerTargetCoordinates[1] - CursorCoordinates[1]))

        distanceDirect = math.sqrt((distanceXY[0]) ** 2 + (distanceXY[1]) ** 2)
        distanceDirect = scipy.special.round(distanceDirect * 100) / 100

        outputCursorDistance = (distanceXY[0], distanceXY[1], distanceDirect)

    if not digitTaskPresent:
        outputuserNumber = -10
        outputgoalNumber = -10
        outputLengthOfUserNumber = 0
        outputLengthofGoalNumber = 0
    else:
        outputLengthOfUserNumber = len(enteredDigitsStr)
        outputLengthofGoalNumber = len(goalNumber)

    if outputuserNumber == "":
        outputuserNumber = -10

    outputText = \
        str(subjNr) + ";" + \
        str(currentTime) + ";" + \
        str(trialTime) + ";" + \
        str(blockNumber) + ";" + \
        str(trialNumber) + ";" + \
        partOfExperiment + ";" + \
        str(trackingTaskPresent) + ";" + \
        str(digitTaskPresent) + ";" + \
        str(trackerWindowVisible) + ";" + \
        str(digitWindowVisible) + ";" + \
        str(trackingWindowVisitCounter) + ";" + \
        str(digitWindowVisitCounter) + ";" + \
        str(radiusAroundTarget) + ";" + \
        str(standardDeviationOfNoise) + ";" + \
        str(outputCursorDistance[0]) + ";" + \
        str(outputCursorDistance[1]) + ";" + \
        str(outputCursorDistance[2]) + ";" + \
        str(outputCursorCoordinates[0]) + ";" + \
        str(outputCursorCoordinates[1]) + ";" + \
        str(outputTrackerTargetCoordinates[0]) + ";" + \
        str(outputTrackerTargetCoordinates[1]) + ";" + \
        str(outputcursorMotion[0]) + ";" + \
        str(outputcursorMotion[1]) + ";" + \
        str(outputuserNumber) + ";" + \
        str(outputgoalNumber) + ";" + \
        str(numberCompleted) + ";" + \
        str(outputLengthOfUserNumber) + ";" + \
        str(outputLengthofGoalNumber) + ";" + \
        str(Eventmessage1) + ";" + \
        str(message2) + "\n"

    outputFile.write(outputText)


def checkKeyPresses():
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global enteredDigitsStr
    global joystickObject  # the joystick object
    global cursorMotion
    global digitTaskWindowSize
    global mousePressed
    global incorrectDigits
    global visitDigits
    global visitIncorrectDigitsNum

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
                writeParticipantDataFile("ButtonRelease", "none")
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeParticipantDataFile("ButtonPress", "none")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePressed = True
            pos = pygame.mouse.get_pos()
            posString = str(pos[0]) + "_" + str(pos[1])
            writeParticipantDataFile("MousePress", posString)

        elif event.type == pygame.KEYDOWN:
            # only process keypresses if the digit task is present
            if digitTaskPresent and digitWindowVisible:
                if event.key == pygame.K_0 or event.key == pygame.K_KP0:
                    keyPressed = "0"
                elif event.key == pygame.K_1 or event.key == pygame.K_KP1:
                    keyPressed = "1"
                elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                    keyPressed = "2"
                elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                    keyPressed = "3"
                elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                    keyPressed = "4"
                elif event.key == pygame.K_5 or event.key == pygame.K_KP5:
                    keyPressed = "5"
                elif event.key == pygame.K_6 or event.key == pygame.K_KP6:
                    keyPressed = "6"
                elif event.key == pygame.K_7 or event.key == pygame.K_KP7:
                    keyPressed = "7"
                elif event.key == pygame.K_8 or event.key == pygame.K_KP8:
                    keyPressed = "8"
                elif event.key == pygame.K_9 or event.key == pygame.K_KP9:
                    keyPressed = "9"
                elif event.key == pygame.K_BACKSPACE or event.key == pygame.K_MINUS or event.key == pygame.K_KP_ENTER \
                        or event.key == pygame.K_KP_MINUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_KP_MULTIPLY:
                    keyPressed = "-"
                elif event.key == pygame.K_F4:
                    quit_app()
                    raise Exception("F4 key pressed and program terminated")
                else:
                    return

                digitPressTimes.append(time.time())
                if len(enteredDigitsStr) < len(goalNumber):
                    if keyPressed == goalNumber[len(enteredDigitsStr)]:
                        enteredDigitsStr = enteredDigitsStr + keyPressed
                        newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 1))
                        while newpart == goalNumber[-1]:
                            newpart = ''.join(random.sample(numbersAvailableForGoalNumber, 1))
                        goalNumber = goalNumber + newpart
                        writeParticipantDataFile("keypress", keyPressed)
                        visitDigits = visitDigits + 1
                    else:
                        writeParticipantDataFile("wrongKeypress", keyPressed)
                        incorrectDigits = incorrectDigits + 1
                        visitIncorrectDigitsNum = visitIncorrectDigitsNum + 1
                else:
                    writeParticipantDataFile("stringTypedTooLong", keyPressed)

                blockMaskingOldLocation = pygame.Surface((int(digitTaskWindowSize[0] - (topLeftCornerOfGoalNumber[0] - topLeftCornerOfDigitTaskWindow[0])), 100)).convert()
                blockMaskingOldLocation.fill(backgroundColorDigitScreen)
                screen.blit(blockMaskingOldLocation, topLeftCornerOfGoalNumber)

                # then post new message
                f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
                goalNumberMessage = f.render(goalNumber[len(enteredDigitsStr):(len(enteredDigitsStr) + 27)], True, (0, 0, 0))
                screen.blit(goalNumberMessage, topLeftCornerOfGoalNumber)


def switchWindows(message):
    print("FUNCTION: " + getFunctionName())
    global digitWindowVisible

    # switching is only done in dual-task
    if partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask":
        if message == "openTracking":
            if trackingTaskPresent:
                openTrackerWindow()
            if digitWindowVisible and digitTaskPresent:
                closeDigitWindow()
        elif message == "closeTracking":
            if trackingTaskPresent:
                closeTrackerWindow()
            if (not digitWindowVisible) and digitTaskPresent:
                openDigitWindow()


def updateTrackerScreen(sleepTime):
    global screen
    global TrackerTargetCoordinates
    global CursorCoordinates
    global trackerdistanceArray
    global numberCompleted
    global startTime
    global maxTrialTimeDual
    global maxTrialTimeSingleTyping
    global cursorMotion
    global trackerWindowVisible

    global stepSizeOfTrackerScreenUpdate

    x = CursorCoordinates[0]
    y = CursorCoordinates[1]
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

    writeParticipantDataFile("none", "none")

    # store distance between cursor and target in array of scores
    distance = math.sqrt((abs(CursorCoordinates[0] - TrackerTargetCoordinates[0])) ** 2 + (abs(CursorCoordinates[1] - TrackerTargetCoordinates[1])) ** 2)
    trackerdistanceArray.append(distance)


def printTextOverMultipleLines(text, fontsize, color, location):
    global screen

    splittedText = text.split("\n")
    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location[0]
    PositionY = location[1]

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        feedbackmessage = f.render(lines, True, color)
        screen.blit(feedbackmessage, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def GiveMessageOnScreen(message, timeMessageIsOnScreen):
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

        message = "Mach dich bereit!\n\n       " + str(timeMessageIsOnScreen - i)

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

    message = "Experimentalleiter bitte hier drücken."
    printTextOverMultipleLines(message, fontsize, color, location)

    pygame.display.flip()

    while not mousePressed:  # wait for a mouseclick
        checkKeyPresses()
        time.sleep(0.25)

    mousePressed = False


def reportUserScore():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global scoresForPayment
    global incorrectDigits
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
    scoresOnThisBlock = [] # stores the scores on the current block. Can be used to report performance each 5th trial

    if partOfExperiment == "dualTask":
        score = duringTrialScore  # use score generated by updateIntermediateScore()

        feedbackScore = score
        if score > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        scoresForPayment.append(score)
        scoresOnThisBlock.append(score)  # store score, so average performance can be reported
        scoreForLogging = score

    elif partOfExperiment == "singleTaskTracking":
        feedbackText = "Deine maximale Distanz: \n"
        if trackingTaskPresent:
            maxTrackerDistance = max(trackerdistanceArray) if len(trackerdistanceArray) > 0 else 0
            # round values
            maxTrackerDistance = scipy.special.round(maxTrackerDistance * 10) / 10
            feedbackText = feedbackText + "\n\n" + str(maxTrackerDistance) + "  pixels"
            scoresOnThisBlock.append(maxTrackerDistance)
            scoreForLogging = maxTrackerDistance

    elif partOfExperiment == "singleTaskTyping":
        feedbackText = "Anzahl Fehler: \n"
        if digitTaskPresent:
            digitScore = digitPressTimes[-1] - digitPressTimes[0]
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText = feedbackText + "\n\n" + str(incorrectDigits) + "  Fehler"
            scoresOnThisBlock.append(incorrectDigits)
            scoreForLogging = digitScore

    if feedbackText != "":
        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)
        printTextOverMultipleLines(feedbackText, fontsize, color, location)

    pygame.display.flip()
    writeParticipantDataFile("scoreGiven", str(scoreForLogging))
    time.sleep(timeFeedbackIsGiven)

    if len(scoresOnThisBlock) % 5 == 0 and len(scoresOnThisBlock) > 0:  # every fifth trial, report mean score
        # prepare background
        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))
        messageAreaObject = pygame.Surface((ExperimentWindowSize[0] - 100, ExperimentWindowSize[1] - 100)).convert()
        messageAreaObject.fill((255, 255, 255))
        topCornerOfMessageArea = (50, 50)
        screen.blit(messageAreaObject, topCornerOfMessageArea)  # make area 50 pixels away from edges

        feedbackText2 = "Deine durchschnittliche Punktzahl der letzten 4 Durchgänge:\n\n"
        meanscore = scipy.special.round(scipy.mean(scoresOnThisBlock[-2:]) * 100) / 100  # report meanscore
        feedbackText2 = feedbackText2 + str(meanscore)
        if partOfExperiment == "singleTaskTracking":
            feedbackText2 = feedbackText2 + " pixels"
        elif partOfExperiment == "singleTaskTyping":
            feedbackText2 = feedbackText2 + " errors"
        elif partOfExperiment == "dualTask":
            feedbackText2 = "Block " + str(int(len(scoresOnThisBlock) / 3)) + " von 6 vollständig. Deine durchschnittliche Leistung der letzten 4 Durchgänge:\n\n" \
                            + str(meanscore) + " points"

        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)

        printTextOverMultipleLines(feedbackText2, fontsize, color, location)
        pygame.display.flip()

        writeParticipantDataFile("avscoreGiven", str(meanscore))
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


def drawowncircle(image, colour, origin, radius, width=0):
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
    global visitIncorrectDigitsNum
    global trackerdistanceArray
    global visitStartTime

    visitStartTime = time.time()
    print("start time:")
    print(visitStartTime)

    trackerdistanceArray = []
    outsideRadius = False
    visitDigits = 0
    visitIncorrectDigitsNum = 0

    digitWindowVisitCounter = digitWindowVisitCounter + 1

    # draw background
    bg = pygame.Surface(digitTaskWindowSize).convert()
    bg.fill((255, 255, 255))
    screen.blit(bg, topLeftCornerOfDigitTaskWindow)  # make area about 30 away from centre

    f = pygame.font.Font(None, fontsizeGoalAndUserNumber)
    goalNumberMessage = f.render(goalNumber[len(enteredDigitsStr):(len(enteredDigitsStr) + 27)], True,
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
        updateIntermediateScoreAndWriteSummaryDataFile()

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(backgroundColorTrackerScreen)

    trackingWindowVisitCounter = trackingWindowVisitCounter + 1

    # draw a filled circle
    drawowncircle(bg, radiusInnerColor,
                  (int(TrackingTaskWindowSize[0] / 2), int(TrackingTaskWindowSize[1] / 2)),
                  radiusAroundTarget, 0)

    # draw edges think
    # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size.
    #  The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.
    drawowncircle(bg, radiusOuterColor,
                  (int(TrackingTaskWindowSize[0] / 2), int(TrackingTaskWindowSize[1] / 2)),
                  radiusAroundTarget, 5)

    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre

    newLocation = (CursorCoordinates[0] - (CursorSize[0] / 2), CursorCoordinates[1] - (CursorSize[1] / 2))
    blockAtNewLocation = pygame.Surface(CursorSize).convert()
    blockAtNewLocation.fill(CursorColor)
    screen.blit(blockAtNewLocation, newLocation)  # blit puts something new on the screen  (should not contain too much info!!)
    trackerWindowVisible = True

    # get the cursor angle
    measuredMotion = (joystickObject.get_axis(0), joystickObject.get_axis(1))
    cursorMotion = (measuredMotion[0], measuredMotion[1])

    if partOfExperiment == "dualTask" or partOfExperiment == "practiceDualTask":
        intermediateMessage = str(visitScore) + " Punkte"
        fontsize = fontsizeGoalAndUserNumber
        color = (0, 0, 0)
        location = (900, 65)
        printTextOverMultipleLines(intermediateMessage, fontsize, color, location)


def updateIntermediateScoreAndWriteSummaryDataFile():
    print("FUNCTION: " + getFunctionName())
    global duringTrialScore  # cumulative score for the current trial
    global outsideRadius  # boolean - did the cursor leave the circle
    global visitDigits  # number of correctly typed digits
    global visitIncorrectDigitsNum  # number of incorrectly typed digits
    global trackerdistanceArray
    global radiusAroundTarget
    global visitScore  # Score for one visit to the digit window
    global visitStartTime
    global visitEndTime
    global CursorColor
    global penalty

    writeMaxDistance = max(trackerdistanceArray) if len(trackerdistanceArray) > 0 else 0

    if len(trackerdistanceArray) == 0:
        writeMeanDistance = 0
    else:
        writeMeanDistance = sum(trackerdistanceArray) / len(trackerdistanceArray)

    if len(trackerdistanceArray) > 0:
        writeEndDistance = trackerdistanceArray[-1]
        writeStartDistance = trackerdistanceArray[0]
    else:
        writeEndDistance = 0
        writeStartDistance = 0

    if writeMaxDistance > radiusAroundTarget:
        outsideRadius = True
        CursorColor = (255, 0, 0)  # red
    else:
        CursorColor = (0, 0, 255)  # blue

    trackerdistanceArray = []
    if outsideRadius:
        if penalty == "lose500":
            # loose 500
            visitScore = ((visitDigits + 10) + (visitIncorrectDigitsNum - 5)) - 500

        if penalty == "loseAll":
            # loose all
            visitScore = 0

        if penalty == "loseHalf":
            # loose half
            visitScore = 0.5 * ((visitDigits * 10) + (visitIncorrectDigitsNum * -5))  # penalty for exit is to lose half points
    else:
        visitScore = (visitDigits * 10) + (visitIncorrectDigitsNum * -5)  # gain is 10 for correct digit and -5 for incorrect digit

    # add the score for this digit task visit to the overall trial score
    # duringtrial score is used in reportUserScore
    duringTrialScore = duringTrialScore + visitScore

    visitTime = visitEndTime - visitStartTime
    writeSummaryDataFile(visitTime, outsideRadius, writeMaxDistance, writeMeanDistance, writeStartDistance, writeEndDistance)
    outsideRadius = False


def runSingleTaskTypingTrials(isPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeSingleTyping
    global numberCompleted
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global goalNumber
    global numberCompleted
    global enteredDigitsStr
    global trackingTaskPresent
    global digitTaskPresent
    global partOfExperiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global digitWindowVisible
    global trackingWindowVisitCounter
    global digitWindowVisitCounter
    global incorrectDigits

    blockNumber = blockNumber + 1
    numberOfTrials = numberOfSingleTaskTypingTrials

    if isPracticeTrial:
        partOfExperiment = "practiceTyping"
        numberOfTrials = 2
        GiveMessageOnScreen("Nur Tippen\n\n"
                            "In diesen Durchgängen führst du nur die Tippaufgabe aus.\n"
                            "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                            "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                            "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren)", 15)
    else:
        partOfExperiment = "singleTaskTyping"
        GiveMessageOnScreen("Nur Tippen\n\n"
                            "Kopiere die Ziffern so schnell wie möglich", 5)

    for i in range(0, numberOfTrials):
        incorrectDigits = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events
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
            enteredDigitsStr = ""
            digitPressTimes = [startTime]

            if digitWindowVisible:
                openDigitWindow()
            else:
                closeDigitWindow()

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (not numberCompleted) and ((time.time() - startTime) < maxTrialTimeSingleTyping) and environmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates

            pygame.display.flip()
            time.sleep(0.02)

        if (time.time() - startTime) >= maxTrialTimeSingleTyping:
            writeParticipantDataFile("trialStopTooMuchTime", "none")
        elif not environmentIsRunning:
            writeParticipantDataFile("trialStopEnvironmentStopped", "none")
        else:
            writeParticipantDataFile("trialStop", "none")

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def runSingleTaskTrackingTrials(isPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeSingleTracking
    global numberCompleted
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global TrackerTargetCoordinates
    global CursorCoordinates
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

    blockNumber = blockNumber + 1
    numberOfTrials = numberOfSingleTaskTrackingTrials

    if isPracticeTrial:
        partOfExperiment = "practiceTracking"
        GiveMessageOnScreen(
            "Nur Tracking\n\n"
            "In diesen Durchgängen führst du nur die Tracking Aufgabe aus.\n"
            "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie der Cursor umher wandert.\n"
            "Der Cursor bewegt sich so lange frei herum, bis du ihn bewegst.",
            15)
        numberOfTrials = 2
    else:
        partOfExperiment = "singleTaskTracking"
        GiveMessageOnScreen(
            "Nur Tracking\n\n"
            "Nutze die Durchgänge, um die Geschwindigkeit des Cursors einschätzen zu können, \n"
            "aber halte den Cursor innerhalb des Kreises",
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

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while ((time.time() - startTime) < maxTrialTimeSingleTracking) and environmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates

            if trackingTaskPresent:
                updateTrackerScreen(0.02)

            pygame.display.flip()

        if not environmentIsRunning:
            writeParticipantDataFile("trialEnvironmentRunning", "none")
        else:
            writeParticipantDataFile("trialEnvironmentStopped", "none")


def runDualTaskTrials(isPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeDual
    global numberCompleted
    global trackerdistanceArray  # an array in which rms distance between target and cursor is stored
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global TrackerTargetCoordinates
    global CursorCoordinates
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
    global incorrectDigits
    global duringTrialScore
    global outsideRadius
    global visitDigits
    global visitStartTime
    global visitEndTime

    blockNumber = blockNumber + 1

    numberOfTrials = numberOfDualTaskTrials

    if isPracticeTrial:
        maxTrialTimeDual = 120
        partOfExperiment = "practiceDualTask"
        GiveMessageOnScreen(
            "Tracking + Tippen\n\n"
            "Du führst jetzt beide Aufgaben gleichzeitig aus.\n"
            "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n"
            "Drücke den Schalter unter deinem Zeigefinger am Joystick, um die Trackingaufgabe zu kontrollieren.\n"
            "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n"
            "Du kannst immer nur eine Aufgabe bearbeiten.",15)
        GiveMessageOnScreen("Dein Ziel:\n"
                            "Kopiere die Ziffern so schnell wie möglich (so gewinnst du Punkte),\n"
                            "aber halte den Cursor innerhalb des Kreises (sonst verlierst du Punkte)\n"
                            "Fehler beim Tippen führen auch zu einem Punktverlust",10)
        
        numberOfTrials = 2
    else:
        maxTrialTimeDual = 120
        partOfExperiment = "dualTask"
        GiveMessageOnScreen("Tracking + Tippen\n\n"
                            "Kopiere die Ziffern so schnell wie möglich (so gewinnst du Punkte),\n"
                            "aber halte den Cursor innerhalb des Kreises (sonst verlierst du Punkte).\n"
                            "Fehler beim Tippen führen auch zu einem Punktverlust.\n\n"
                            "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl.", 18)
        GiveMessageOnScreen("Der Cursor bewegt sich mit derselben Geschwindigkeit wie zuvor.\n"
                            "Der Kreis hat dieselbe Größe\n\n"
                            "Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                            "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                            "Du kannst immer nur eine Aufgabe bearbeiten." ,15)

    for i in range(0, numberOfTrials):
        duringTrialScore = 0
        outsideRadius = False
        visitDigits = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events

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
            enteredDigitsStr = ""
            digitPressTimes = [startTime]
            if digitWindowVisible:
                openDigitWindow()
            else:
                closeDigitWindow()

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (not numberCompleted) and ((time.time() - startTime) < maxTrialTimeDual) and environmentIsRunning:
            checkKeyPresses()  # checks keypresses for both the trackingtask and the digittask and starts relevant display updates
            if trackingTaskPresent:
                updateTrackerScreen(0.02)
            pygame.display.flip()

        visitEndTime = time.time()
        updateIntermediateScoreAndWriteSummaryDataFile()

        if (time.time() - startTime) >= maxTrialTimeDual:
            writeParticipantDataFile("trialStopTooMuchTime", "none")
        elif not environmentIsRunning:
            writeParticipantDataFile("trialStopEnvironmentStopped", "none")
        else:
            writeParticipantDataFile("trialStop", "none")

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def readInputAndCreateOutputFiles(subjNrStr):
    print("FUNCTION: " + getFunctionName())
    """
    Read the participant file / set the participant condition.
    Initialize the output files
    """
    global conditions
    global outputFile
    global summaryOutputFile

    f = open('participantConditions.csv','r')
    individualLines = f.read().split('\n') ## read by lines
    lines = list(map(lambda x: x.split(';'), individualLines) )     #split all elements
    subjectLine = []
    for line in lines:
        if line[0] == subjNrStr:
            if not subjectLine:
                subjectLine = line[1:]
            else:
                raise Exception("Duplicate subject number")
    if not subjectLine:
        raise Exception("Invalid subject number")

    conditions = subjectLine
    f.close()

    timestamp = time.strftime("%Y-%m-%d_%H-%M")

    fileName = "participant_" + subjNrStr + "_data_"  + timestamp + ".csv"
    outputFile = open(fileName, 'w')  # contains the user data
    outputText = "SubjectNr;" \
                 "CurrentTime;" \
                 "LocalTime;" \
                 "BlockNumber;" \
                 "TrialNumber;" \
                 "partOfExperiment;" \
                 "TrackingTaskPresent;" \
                 "DigitTaskPresent;" \
                 "TrackerWindowVisible;" \
                 "DigitWindowVisible;" \
                 "TrackingWindowVisitCounter;" \
                 "DigitWindowVisitCounter;" \
                 "RadiusAroundTarget;" \
                 "standardDeviationOfNoise;" \
                 "CursorDistanceX;" \
                 "CursorDistanceY;" \
                 "CursorDistanceDirect;" \
                 "CursorCoordinatesX;" \
                 "CursorCoordinatesY;" \
                 "TrackerTargetCoordinatesX;" \
                 "TrackerTargetCoordinatesY;" \
                 "cursorMotionX;" \
                 "cursorMotionY;" \
                 "userNumber;" \
                 "goalNumber;" \
                 "numberCompleted;" \
                 "LengthOfUserNumber;" \
                 "LengthofGoalNumber;" \
                 "Eventmessage1;" \
                 "Eventmessage2" + "\n"
    outputFile.write(outputText)

    ########################Second Output File######################################

    summaryFileName = "participant" + subjNrStr + "_summary_" + timestamp + ".csv"
    summaryOutputFile = open(summaryFileName, 'w')  # contains the user data
    summaryOutputText = "SubjectNr;"\
                        "BlockNumber;"\
                        "TrialNumber;"\
                        "partOfExperiment;"\
                        "standardDeviationOfNoise;"\
                        "visitTime;"\
                        "visitCorrectDigits;"\
                        "visitIncorrectDigitsNum;"\
                        "visitScore;"\
                        "outsideRadius;"\
                        "maxDistance;"\
                        "meanDistance;"\
                        "endDistance;"\
                        "startDistance;" + "\n"
    summaryOutputFile.write(summaryOutputText)


def main():
    global screen
    global environmentIsRunning  # variable that states that there is a main window
    global conditions
    global radiusAroundTarget
    global numbersAvailableForGoalNumber
    global scoresForPayment
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment
    global penalty
    global currentCondition
    global subjNr

    subjNrStr = input("Please enter the subject number here: ")
    subjNr = int(subjNrStr)
    firstTrial = input("First trial? (yes/no) ")
    showPrecedingPenaltyInfo = input("Show penalty and noise information before the experiment starts? (yes/no) ")
    readInputAndCreateOutputFiles(subjNrStr)
    timeOfCompleteStartOfExperiment = time.time()

    pygame.init()
    screen = pygame.display.set_mode(ExperimentWindowSize, pygame.FULLSCREEN)
    pygame.display.set_caption("Multitasking 2.0")
    environmentIsRunning = True

    ShowStartExperimentScreen()

    # verify all conditions before the experiment starts so that the program would crash at the start if it does
    conditionsVerified = []
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

        conditionsVerified.append({
            "standardDeviationOfNoise": standardDeviationOfNoise,
            "noiseMsg": noiseMsg,
            "radiusAroundTarget": radiusAroundTarget,
            "numbersAvailableForGoalNumber": numbersAvailableForGoalNumber,
            "penalty": penalty,
            "penaltyMsg": penaltyMsg
        })

    if firstTrial == "yes":
        GiveMessageOnScreen("Willkommen zum Experiment!\n\n\n"
                            "Wir beginnen mit 3 Probedurchläufen.", 10)
        numbersAvailableForGoalNumber = "123123123"
        # do practice trials
        runSingleTaskTrackingTrials(True)
        runSingleTaskTypingTrials(True)
        runDualTaskTrials(True)
        GiveMessageOnScreen("Jetzt testen wir deine Leistung in diesen Aufgaben. \n"
                            "Versuche so viele Punkte wie möglich zu gewinnen", 10)

    # main experiment loop with verified conditions
    for condition in conditionsVerified:
        print("condition: " + str(condition))
        # set global and local variables
        standardDeviationOfNoise = condition["standardDeviationOfNoise"]
        noiseMsg = condition["noiseMsg"]
        radiusAroundTarget = condition["radiusAroundTarget"]
        numbersAvailableForGoalNumber = condition["numbersAvailableForGoalNumber"]
        penalty = condition["penalty"]
        penaltyMsg = condition["penaltyMsg"]

        if showPrecedingPenaltyInfo == "yes":
            message = "NEUER BLOCK: \n\n\n" \
                      "In den folgenden Durchgängen bewegt sich der Cursor mit " + noiseMsg + " Geschwindigkeit. \n" \
                      "Für jede korrekt eingegebene Ziffer bekommst du 10 Punkte. \n" \
                      "Bei jeder falsch eingetippten Ziffer verlierst du 5 Punkte. \n" \
                      "Wenn der Cursor den Kreis verlässt, verlierst du " + penaltyMsg + " deiner Punkte."
        else:
            message = "NEUER BLOCK: \n\n\n" \
                      "In den folgenden Durchgängen bewegt sich der Cursor mit " + noiseMsg + " Geschwindigkeit. \n" \
                      "Für jede korrekt eingegebene Ziffer bekommst du Punkte. \n" \
                      "Du verlierst Punkte für falsch eingegebene Ziffern und wenn der Punkt den Kreis verlässt."
        GiveMessageOnScreen(message, 10)

        runSingleTaskTrackingTrials(False)
        runSingleTaskTypingTrials(False)
        runDualTaskTrials(False)

        message = "Bisher hast du: " + str(scipy.sum(scoresForPayment)) + " Punkte"
        GiveMessageOnScreen(message, 8)

    GiveMessageOnScreen("Dies ist das Ende der Studie.", 5)

    quit_app()


def quit_app():
    global environmentIsRunning
    global outputFile
    global summaryOutputFile

    environmentIsRunning = False
    pygame.display.quit()
    pygame.quit()
    outputFile.close()
    summaryOutputFile.close()


def getFunctionName():
    return inspect.stack()[1][3]


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        stack = traceback.format_exc()
        with open("Log_Exceptions.txt", "a") as log:
            log.write(f"{datetime.datetime.now()} {str(e)}   {str(stack)} \n")
            print(str(e))
            print(str(stack))


