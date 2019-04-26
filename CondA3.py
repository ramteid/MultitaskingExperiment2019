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
import random
import time
import traceback

import math
import pygame
import scipy
import scipy.special
import datetime

######initialize global variables

incorrectDigits = 0
trialScore = 0
outsideRadius = False
correctlyTypedDigitsInVisit = 0
incorrectlyTypedDigitsInVisit = 0
visitScore = 0
visitEndTime = 0
visitStartTime = 0

global penalty
penalty = ""

global fullscreen
fullscreen = True

timeFeedbackIsGiven = 4

global numberOfCircleExits
numberOfCircleExits = 0

global environmentIsRunning  # True if there is a display
global joystickObject  # the joystick object (initialized at start of experiment)
global experiment
experiment = "singleTaskTracking"
global outputFile
global summaryOutputFile
global conditions
conditions = ()
joystickAxis = (0, 0)  # the motion of the joystick
digitPressTimes = []
startTime = 0
timeFeedbackIsShown = 4
backgroundColorTrackerScreen = (255, 255, 255)  # white
backgroundColorDigitScreen = backgroundColorTrackerScreen
backgroundColorEntireScreen = (50, 50, 50)  # gray
coverUpColor = (200, 200, 200)  # very light gray
radiusInnerColor = (255, 204, 102)  # orange
radiusOuterColor = (255, 0, 0)  # red
cursorColor = (0, 0, 255)  # blue

ExperimentWindowSize = (1280, 1024)  # eye-tracker screen: 1280*1024 pixels
TrackingTaskWindowSize = typingTaskWindowSize = (450, 450)
cursorSize = (20, 20)

topLeftCornerOfTypingTaskWindow = (int(ExperimentWindowSize[0] - TrackingTaskWindowSize[0] - typingTaskWindowSize[0]) / 3, 50)
topLeftCornerOfTrackingTaskWindow = (2 * topLeftCornerOfTypingTaskWindow[0] + typingTaskWindowSize[0], 50)

topLeftCornerOfTypingTaskNumber = (typingTaskWindowSize[0] / 2 - 150 + topLeftCornerOfTypingTaskWindow[0],
                             typingTaskWindowSize[1] / 2 - 20 + topLeftCornerOfTypingTaskWindow[1])
topLeftCornerOfTypingTaskNumber = (typingTaskWindowSize[0] / 2 - 150 + topLeftCornerOfTypingTaskWindow[0],
                                   typingTaskWindowSize[1] / 2 + 20 + topLeftCornerOfTypingTaskWindow[1])
availableTypingTaskNumbers = "123456789"
generatedTypingTaskNumbers = "123456789"
typingTaskNumbersCount = 27
enteredDigitsStr = ""

cursorCoordinates = (TrackingTaskWindowSize[0] / 2 - (cursorSize[0] / 2), TrackingTaskWindowSize[1] / 2 - (cursorSize[0] / 2))

fontsizeGoalAndTypingTaskNumber = 30

maxTrialTimeDual = 120  # maximum time for dual-task trials
maxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
maxTrialTimeSingleTyping = 20  # maximum time for single-task typing

numberOfDualTaskTrials = 3
numberOfSingleTaskTrackingTrials = 2
numberOfSingleTaskTypingTrials = 2

trackingWindowEntryCounter = 0
typingWindowEntryCounter = 0

trackingTaskPresent = True
typingTaskPresent = True

scalingJoystickAxis = 5  # how many pixels does the cursor move when joystick is at full angle (value of 1 or -1).

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
global typingWindowVisible
typingWindowVisible = True

radiusCircle = 100
standardDeviationOfNoise = -1
stepSizeOfTrackerScreenUpdate = 0.005  # how many seconds does it take for a screen update?
scoresForPayment = []
baseratePayment = 0
maxPayment = 15  # what do we pay maximum?
timeOfCompleteStartOfExperiment = 0  # this value is needed because otherwise one of the time output numbers becomes too large to have enough precision


def writeSummaryDataFile(visitTime, outsideRadius1):
    print("FUNCTION: " + getFunctionName())
    global summaryOutputFile
    global subjNr
    global experiment
    global blockNumber
    global trialNumber
    global standardDeviationOfNoise
    global visitScore
    global correctlyTypedDigitsInVisit
    global incorrectlyTypedDigitsInVisit

    summaryOutputText = \
        str(subjNr) + ";" + \
        str(blockNumber) + ";" + \
        str(trialNumber) + ";" + \
        experiment + ";" + \
        str(standardDeviationOfNoise) + ";" + \
        str(visitTime) + ";" + \
        str(correctlyTypedDigitsInVisit) + ";" + \
        str(incorrectlyTypedDigitsInVisit) + ";" + \
        str(visitScore) + ";" + \
        str(outsideRadius1) + "\n"

    summaryOutputFile.write(summaryOutputText)


def writeParticipantDataFile(eventMessage1, eventMessage2):
    global outputFile
    global subjNr
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global generatedTypingTaskNumbers
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global experiment
    global blockNumber
    global trialNumber
    global cursorCoordinates
    global joystickAxis
    global startTime  # stores time at which trial started
    global trackerWindowVisible
    global typingWindowVisible
    global radiusCircle
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment  # time at which experiment started
    global numberOfCircleExits
    global trialScore

    currentTime = time.time() - timeOfCompleteStartOfExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracker)
    currentTime = scipy.special.round(currentTime * 10000) / 10000

    trialTime = time.time() - startTime  # this is a local time (reset at the start of each trial) in seconds
    trialTime = scipy.special.round(trialTime * 10000) / 10000

    if not trackingTaskPresent:
        outputCursorCoordinateX = "-"
        outputCursorCoordinateY = "-"
        outputJoystickAxisX = "-"
        outputJoystickAxisY = "-"
    else:
        outputCursorCoordinateX = scipy.special.round(cursorCoordinates[0] * 100) / 100
        outputCursorCoordinateY = scipy.special.round(cursorCoordinates[1] * 100) / 100
        outputJoystickAxisX = scipy.special.round(joystickAxis[0] * 1000) / 1000
        outputJoystickAxisY = scipy.special.round(joystickAxis[1] * 1000) / 1000

    if typingTaskPresent:
        outputEnteredDigitsStr = enteredDigitsStr
        outputTypingTaskNumberLength = len(enteredDigitsStr)
        outputGeneratedTypingTaskNumbers = generatedTypingTaskNumbers
        outputGeneratedTypingTaskNumbersLength = len(generatedTypingTaskNumbers)
    else:
        outputEnteredDigitsStr = "-"
        outputTypingTaskNumberLength = "-"
        outputGeneratedTypingTaskNumbers = "-"
        outputGeneratedTypingTaskNumbersLength = "-"

    outputText = \
        str(subjNr) + ";" + \
        str(currentTime) + ";" + \
        str(trialTime) + ";" + \
        str(blockNumber) + ";" + \
        str(trialNumber) + ";" + \
        experiment + ";" + \
        str(trackingTaskPresent) + ";" + \
        str(typingTaskPresent) + ";" + \
        str(trackerWindowVisible) + ";" + \
        str(typingWindowVisible) + ";" + \
        str(trackingWindowEntryCounter) + ";" + \
        str(typingWindowEntryCounter) + ";" + \
        str(radiusCircle) + ";" + \
        str(standardDeviationOfNoise) + ";" + \
        str(outputCursorCoordinateX) + ";" + \
        str(outputCursorCoordinateY) + ";" + \
        str(outputJoystickAxisX) + ";" + \
        str(outputJoystickAxisY) + ";" + \
        str(outputEnteredDigitsStr) + ";" + \
        str(outputGeneratedTypingTaskNumbers) + ";" + \
        str(outputTypingTaskNumberLength) + ";" + \
        str(outputGeneratedTypingTaskNumbersLength) + ";" + \
        str(numberOfCircleExits) + ";" + \
        str(trialScore) + ";" + \
        str(eventMessage1) + ";" + \
        str(eventMessage2) + "\n"

    outputFile.write(outputText)


def checkMouseClicked():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_app()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            posString = str(pos[0]) + "_" + str(pos[1])
            writeParticipantDataFile("MousePressed", posString)
            return pos[0], pos[1]
    return False


def checkKeyPressed():
    global digitPressTimes  # stores the intervals between keypresses
    global generatedTypingTaskNumbers
    global enteredDigitsStr
    global joystickObject  # the joystick object
    global joystickAxis
    global typingTaskWindowSize
    global incorrectDigits
    global correctlyTypedDigitsInVisit
    global incorrectlyTypedDigitsInVisit
    global cursorCoordinates

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            cursorCoordinates = pos[0], pos[1]
        elif event.type == pygame.QUIT:
            quit_app()
        elif event.type == pygame.JOYAXISMOTION:
            if trackingTaskPresent:
                # values between -1 and 1. (-1,-1) top left corner, (1,-1) top right; (-1,1) bottom left, (1,1) bottom right
                # prevent the program crashing when no joystick is connected
                try:
                    joystickAxis = (joystickObject.get_axis(0), joystickObject.get_axis(1))
                except (pygame.error, NameError):
                    pass
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 0:  # only respond to 0 button
                switchWindows("closeTracking")
                writeParticipantDataFile("ButtonRelease", "none")
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeParticipantDataFile("ButtonPress", "none")

        elif event.type == pygame.KEYDOWN:
            # only process keypresses if the digit task is present
            if typingTaskPresent and typingWindowVisible:
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
                else:
                    return

                digitPressTimes.append(time.time())
                if len(enteredDigitsStr) < len(generatedTypingTaskNumbers):
                    if keyPressed == generatedTypingTaskNumbers[len(enteredDigitsStr)]:
                        enteredDigitsStr = enteredDigitsStr + keyPressed
                        newpart = ''.join(random.sample(availableTypingTaskNumbers, 1))
                        while newpart == generatedTypingTaskNumbers[-1]:
                            newpart = ''.join(random.sample(availableTypingTaskNumbers, 1))
                        generatedTypingTaskNumbers = generatedTypingTaskNumbers + newpart
                        writeParticipantDataFile("keypress", keyPressed)
                        correctlyTypedDigitsInVisit += 1
                    else:
                        writeParticipantDataFile("wrongKeypress", keyPressed)
                        incorrectDigits += 1
                        incorrectlyTypedDigitsInVisit += 1
                else:
                    writeParticipantDataFile("stringTypedTooLong", keyPressed)

                blockMaskingOldLocation = pygame.Surface((int(
                    typingTaskWindowSize[0] - (topLeftCornerOfTypingTaskNumber[0] - topLeftCornerOfTypingTaskWindow[0])), 100)).convert()
                blockMaskingOldLocation.fill(backgroundColorDigitScreen)
                screen.blit(blockMaskingOldLocation, topLeftCornerOfTypingTaskNumber)

                # then post new message
                f = pygame.font.Font(None, fontsizeGoalAndTypingTaskNumber)
                typingTaskNumberMessage = f.render(generatedTypingTaskNumbers[len(enteredDigitsStr):(len(enteredDigitsStr) + 27)], True, (0, 0, 0))
                screen.blit(typingTaskNumberMessage, topLeftCornerOfTypingTaskNumber)


def switchWindows(message):
    print("FUNCTION: " + getFunctionName())
    global typingWindowVisible

    # switching is only done in dual-task
    if experiment == "dualTask" or experiment == "practiceDualTask":
        if message == "openTracking":
            if trackingTaskPresent:
                openTrackerWindow()
            if typingWindowVisible and typingTaskPresent:
                closeTypingWindow()
        elif message == "closeTracking":
            if trackingTaskPresent:
                closeTrackerWindow()
            if (not typingWindowVisible) and typingTaskPresent:
                openTypingWindow()


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

    fontsize = fontsizeGoalAndTypingTaskNumber
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

        topCornerOfMessageArea = (int(ExperimentWindowSize[0] * 2 / 5), int(topLeftCornerOfTypingTaskWindow[1] + 10))
        screen.blit(messageAreaObject, topCornerOfMessageArea)

        message = "Mach dich bereit!\n\n       " + str(timeMessageIsOnScreen - i)

        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 70, topCornerOfMessageArea[1] + 10)

        printTextOverMultipleLines(message, fontsize, color, location)

        pygame.display.flip()
        time.sleep(1)


def ShowStartExperimentScreen():
    global startTime
    print("FUNCTION: " + getFunctionName())

    drawCanvas()

    fontsize = fontsizeGoalAndTypingTaskNumber
    color = (0, 0, 0)
    location = (175, 175)

    message = "Experimentalleiter bitte hier drücken."
    printTextOverMultipleLines(message, fontsize, color, location)

    pygame.display.flip()

    while not checkMouseClicked():  # wait for a mouseclick
        time.sleep(0.25)
    startTime = time.time()


def drawCanvas():
    global screen
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


def reportUserScore():
    print("FUNCTION: " + getFunctionName())
    global screen
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global trackingTaskPresent
    global typingTaskPresent
    global experiment
    global scoresForPayment
    global incorrectDigits
    global trialScore

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
    scoresOnThisBlock = []  # stores the scores on the current block. Can be used to report performance each 5th trial

    if experiment == "dualTask":
        feedbackScore = trialScore
        if trialScore > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        scoresForPayment.append(trialScore)
        scoresOnThisBlock.append(trialScore)  # store score, so average performance can be reported
        scoreForLogging = trialScore

    elif experiment == "singleTaskTyping":
        feedbackText = "Anzahl Fehler: \n"
        if typingTaskPresent:
            digitScore = digitPressTimes[-1] - digitPressTimes[0]
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText += "\n\n" + str(incorrectDigits) + " Fehler"
            scoresOnThisBlock.append(incorrectDigits)
            scoreForLogging = digitScore

    if feedbackText != "":
        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)
        printTextOverMultipleLines(feedbackText, fontsize, color, location)

    pygame.display.flip()
    writeParticipantDataFile("scoreGiven", str(scoreForLogging))
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

        feedbackText2 = "Deine durchschnittliche Punktzahl der letzten 4 Durchgänge:\n\n"
        meanscore = scipy.special.round(scipy.mean(scoresOnThisBlock[-2:]) * 100) / 100  # report meanscore
        feedbackText2 = feedbackText2 + str(meanscore)

        if experiment == "singleTaskTracking":
            feedbackText2 = feedbackText2 + " pixels"
        elif experiment == "singleTaskTyping":
            feedbackText2 = feedbackText2 + " errors"
        elif experiment == "dualTask":
            feedbackText2 = "Block " + str(int(len(
                scoresOnThisBlock) / 3)) + " von 6 vollständig. Deine durchschnittliche Leistung der letzten 4 Durchgänge:\n\n" \
                            + str(meanscore) + " points"

        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)

        printTextOverMultipleLines(feedbackText2, fontsize, color, location)
        pygame.display.flip()

        writeParticipantDataFile("avscoreGiven", str(meanscore))
        time.sleep(20)


def generateTypingTaskNumber():
    print("FUNCTION: " + getFunctionName())
    global generatedTypingTaskNumbers
    global typingTaskNumbersCount

    if typingTaskNumbersCount == 240:
        generatedTypingTaskNumbers = ''.join(random.sample(availableTypingTaskNumbers, typingTaskNumbersCount))
    elif typingTaskNumbersCount < 19:
        generatedTypingTaskNumbers = ''.join(random.sample(availableTypingTaskNumbers, 9))
        newpart = ''.join(random.sample(availableTypingTaskNumbers, 9))
        # prevent situations with repeating digits
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        newpart = newpart[0:(typingTaskNumbersCount - 9)]
        generatedTypingTaskNumbers = generatedTypingTaskNumbers + newpart

    elif typingTaskNumbersCount == 27:  ### changed tp == 27
        generatedTypingTaskNumbers = ''.join(random.sample(availableTypingTaskNumbers, 9))
        newpart = ''.join(random.sample(availableTypingTaskNumbers, 9))
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]

        generatedTypingTaskNumbers = generatedTypingTaskNumbers + newpart

        newpart = ''.join(random.sample(availableTypingTaskNumbers, 9))
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]
        if newpart[0] == generatedTypingTaskNumbers[-1]:
            newpart = newpart[1:] + generatedTypingTaskNumbers[-1]

        newpart = newpart[0:(typingTaskNumbersCount - 18)]
        generatedTypingTaskNumbers = generatedTypingTaskNumbers + newpart


def drawCircles(bg, size):
    # draw a filled circle
    drawCircle(bg, radiusInnerColor,
               (int(size[0] / 2), int(size[1] / 2)),
               radiusCircle, 0)
    # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size.
    #  The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.
    drawCircle(bg, radiusOuterColor,
               (int(size[0] / 2), int(size[1] / 2)),
               radiusCircle, 5)


def drawCircle(image, colour, origin, radius, width=0):
    global cursorCoordinates
    # based on recommendation on pygame website
    if width == 0:
        pygame.draw.circle(image, colour, origin, int(radius))
    else:
        if radius > 65534 / 5:
            radius = 65534 / 5
        circle = pygame.Surface([radius * 2 + width, radius * 2 + width]).convert_alpha()
        circle.fill([0, 0, 0, 0])
        pygame.draw.circle(circle, colour, (int(circle.get_width() / 2), int(circle.get_height() / 2)),
                           int(radius + (width / 2)))
        if int(radius - (width / 2)) > 0:
            pygame.draw.circle(circle, [0, 0, 0, 0], (int(circle.get_width() / 2), int(circle.get_height() / 2)),
                               abs(int(radius - (width / 2))))
        image.blit(circle, [origin[0] - (circle.get_width() / 2), origin[1] - (circle.get_height() / 2)])


def drawCursor(sleepTime):
    global screen
    global cursorCoordinates
    global startTime
    global maxTrialTimeDual
    global maxTrialTimeSingleTyping
    global joystickAxis
    global trackerWindowVisible
    global stepSizeOfTrackerScreenUpdate
    global outsideRadius
    global radiusCircle
    global cursorColor

    x = cursorCoordinates[0]
    y = cursorCoordinates[1]
    final_x = x
    final_y = y

    # only add noise if tracker is not moving
    motionThreshold = 0.08
    if not (trackerWindowVisible and (joystickAxis[0] > motionThreshold or joystickAxis[0] < -1 * motionThreshold or joystickAxis[1] > motionThreshold or joystickAxis[1] < -1 * motionThreshold)):
        final_x = x + random.gauss(0, standardDeviationOfNoise)
        final_y = y + random.gauss(0, standardDeviationOfNoise)

    if trackerWindowVisible:  # only add joystickAxis if the window is open (i.e., if the participant sees what way cursor moves!)
        final_x += joystickAxis[0] * scalingJoystickAxis
        final_y += joystickAxis[1] * scalingJoystickAxis

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)s
    nrUpdates = int(sleepTime / stepSizeOfTrackerScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if trackerWindowVisible:
        for i in range(0, nrUpdates):
            x += delta_x
            y += delta_y

            if (x, y) != cursorCoordinates:
                # now check if the cursor is still within screen range
                if x < (topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2
                elif x > (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - cursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - cursorSize[0] / 2

                if y < (topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2
                elif y > (topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - cursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - cursorSize[1] / 2

                if trackerWindowVisible:  # only update screen when it's visible
                    # now prepare the screen for an update
                    # first do appropriate cover-up
                    oldLocationX = cursorCoordinates[0] - cursorSize[0] / 2
                    oldLocationY = cursorCoordinates[1] - cursorSize[1] / 2  # gives top-left corner of block
                    blockMaskingOldLocation = pygame.Surface(cursorSize).convert()
                    blockMaskingOldLocation.fill(backgroundColorTrackerScreen)
                    screen.blit(blockMaskingOldLocation, (oldLocationX, oldLocationY))

                    windowMiddleX = topLeftCornerOfTrackingTaskWindow[0] + int(TrackingTaskWindowSize[0] / 2.0)
                    windowMiddleY = topLeftCornerOfTrackingTaskWindow[1] + int(TrackingTaskWindowSize[1] / 2.0)

                    distanceCursorMiddle = math.sqrt((abs(windowMiddleX - x)) ** 2 + (abs(windowMiddleY - y)) ** 2)
                    if distanceCursorMiddle > radiusCircle:
                        outsideRadius = True
                        cursorColor = (255, 0, 0)  # red
                    else:
                        outsideRadius = False
                        cursorColor = (0, 0, 255)  # blue

                    # if cursor used to be within radius from target, redraw circle
                    sizeOfLocalScreen = (int(radiusCircle * 2.5), int(radiusCircle * 2.5))
                    localScreen = pygame.Surface(sizeOfLocalScreen).convert()
                    localScreen.fill(backgroundColorTrackerScreen)

                    drawCircles(localScreen, sizeOfLocalScreen)

                    # make area about 30 away from centre
                    screen.blit(localScreen,
                                ((topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] / 2 - sizeOfLocalScreen[0] / 2),
                                 (topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] / 2 - sizeOfLocalScreen[1] / 2)))

                    # always redraw cursor
                    newLocation = (x - cursorSize[0] / 2, y - cursorSize[1] / 2)
                    blockAtNewLocation = pygame.Surface(cursorSize).convert()
                    blockAtNewLocation.fill(cursorColor)

                    # blit puts something new on the screen  (should not contain too much info!!)
                    screen.blit(blockAtNewLocation, newLocation)

            # always update coordinates
            cursorCoordinates = (x, y)
            pygame.display.flip()
            time.sleep(stepSizeOfTrackerScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % stepSizeOfTrackerScreenUpdate
        if mods != 0:
            time.sleep(mods)

    # if tracker window is not visible, just update the values
    else:
        x = final_x
        y = final_y

        # now check if the cursor is still within screen range
        if (x, y) != cursorCoordinates:
            if x < (topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2
            elif x > (topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - cursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + TrackingTaskWindowSize[0] - cursorSize[0] / 2

            if y < (topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2
            elif y > (topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - cursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + TrackingTaskWindowSize[1] - cursorSize[1] / 2
        # if display is not updated, sleep for entire time
        time.sleep(sleepTime)

    # always update coordinates
    cursorCoordinates = (x, y)


def closeTypingWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global typingWindowVisible
    global radiusCircle
    global visitEndTime

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(coverUpColor)

    screen.blit(bg, topLeftCornerOfTypingTaskWindow)  # make area about 30 away from centre
    typingWindowVisible = False
    visitEndTime = time.time()


def openTypingWindow():
    print("FUNCTION: " + getFunctionName())
    global typingWindowVisible
    global typingWindowEntryCounter
    global outsideRadius
    global correctlyTypedDigitsInVisit
    global incorrectlyTypedDigitsInVisit
    global visitStartTime

    visitStartTime = time.time()
    outsideRadius = False
    correctlyTypedDigitsInVisit = 0
    incorrectlyTypedDigitsInVisit = 0

    typingWindowEntryCounter = typingWindowEntryCounter + 1

    drawTypingWindow()

    typingWindowVisible = True


def drawTypingWindow():
    global screen

    bg = pygame.Surface(ExperimentWindowSize).convert()
    bg.fill(backgroundColorEntireScreen)
    screen.blit(bg, (0, 0))

    # draw background
    bg = pygame.Surface(typingTaskWindowSize).convert()
    bg.fill((255, 255, 255))
    screen.blit(bg, topLeftCornerOfTypingTaskWindow)  # make area about 30 away from centre

    f = pygame.font.Font(None, fontsizeGoalAndTypingTaskNumber)
    typingTaskNumberMessage = f.render(generatedTypingTaskNumbers[len(enteredDigitsStr):(len(enteredDigitsStr) + 27)], True, (0, 0, 0))
    screen.blit(typingTaskNumberMessage, topLeftCornerOfTypingTaskNumber)


def closeTrackerWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackerWindowVisible
    global visitEndTime

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(coverUpColor)
    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre
    trackerWindowVisible = False
    visitEndTime = time.time()


def openTrackerWindow():
    print("FUNCTION: " + getFunctionName())
    global trackerWindowVisible
    global trackingWindowEntryCounter
    global joystickAxis
    global visitScore
    global visitStartTime

    visitStartTime = time.time()
    trackingWindowEntryCounter += 1

    if experiment == "dualTask" or experiment == "practiceDualTask":
        updateIntermediateScoreAndWriteSummaryDataFile()

    drawTrackerWindow()

    trackerWindowVisible = True

    # get the cursor angle
    # prevent the program crashing when no joystick is connected
    try:
        joystickAxis = (joystickObject.get_axis(0), joystickObject.get_axis(1))
    except (pygame.error, NameError):
        pass

    if experiment == "dualTask" or experiment == "practiceDualTask":
        intermediateMessage = str(visitScore) + " Punkte"
        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (900, 65)
        printTextOverMultipleLines(intermediateMessage, fontsize, color, location)


def drawTrackerWindow():
    global screen
    global cursorColor
    global cursorCoordinates

    bg = pygame.Surface(ExperimentWindowSize).convert()
    bg.fill(backgroundColorEntireScreen)
    screen.blit(bg, (0, 0))

    # draw background
    bg = pygame.Surface(TrackingTaskWindowSize).convert()
    bg.fill(backgroundColorTrackerScreen)
    drawCircles(bg, TrackingTaskWindowSize)
    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre
    newCursorLocation = (cursorCoordinates[0] - (cursorSize[0] / 2), cursorCoordinates[1] - (cursorSize[1] / 2))
    newCursor = pygame.Surface(cursorSize).convert()
    newCursor.fill(cursorColor)
    screen.blit(newCursor, newCursorLocation)  # blit puts something new on the screen


def updateIntermediateScoreAndWriteSummaryDataFile():
    print("FUNCTION: " + getFunctionName())
    global trialScore  # cumulative score for the current trial
    global outsideRadius  # boolean - did the cursor leave the circle
    global numberOfCircleExits
    global correctlyTypedDigitsInVisit  # number of correctly typed digits
    global incorrectlyTypedDigitsInVisit  # number of incorrectly typed digits
    global radiusCircle
    global visitScore  # Score for one visit to the digit window
    global visitStartTime
    global visitEndTime
    global cursorColor
    global penalty

    if outsideRadius:
        numberOfCircleExits += 1
        if penalty == "lose500":
            # loose 500
            visitScore = ((correctlyTypedDigitsInVisit + 10) + (incorrectlyTypedDigitsInVisit - 5)) - 500

        if penalty == "loseAll":
            # loose all
            visitScore = 0

        if penalty == "loseHalf":
            # loose half
            visitScore = 0.5 * ((correctlyTypedDigitsInVisit * 10) + (incorrectlyTypedDigitsInVisit * -5))  # penalty for exit is to lose half points
    else:
        visitScore = (correctlyTypedDigitsInVisit * 10) + (incorrectlyTypedDigitsInVisit * -5)  # gain is 10 for correct digit and -5 for incorrect digit

    # add the score for this digit task visit to the overall trial score
    # duringtrial score is used in reportUserScore
    trialScore += visitScore

    visitTime = visitEndTime - visitStartTime
    writeSummaryDataFile(visitTime, outsideRadius)
    outsideRadius = False


def runSingleTaskTypingTrials(isPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeSingleTyping
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global generatedTypingTaskNumbers
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global experiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global incorrectDigits
    global numberOfCircleExits
    global trialScore

    blockNumber += 1
    numberOfTrials = numberOfSingleTaskTypingTrials

    if isPracticeTrial:
        experiment = "practiceTyping"
        numberOfTrials = 2
        GiveMessageOnScreen("Nur Tippen\n\n"
                            "In diesen Durchgängen führst du nur die Tippaufgabe aus.\n"
                            "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                            "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                            "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren.)", 15)
    else:
        experiment = "singleTaskTyping"
        GiveMessageOnScreen("Nur Tippen\n\n"
                            "Kopiere die Ziffern so schnell wie möglich", 5)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        incorrectDigits = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events
        trackerWindowVisible = False
        typingWindowVisible = True

        trackingTaskPresent = False
        typingTaskPresent = True
        trialNumber = trialNumber + 1
        trackingWindowEntryCounter = 0
        typingWindowEntryCounter = 0

        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        startTime = time.time()

        if typingTaskPresent:
            generateTypingTaskNumber()
            enteredDigitsStr = ""
            digitPressTimes = [startTime]

            if typingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (time.time() - startTime) < maxTrialTimeSingleTyping and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates
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
    global startTime  # stores time at which trial starts
    global trackingTaskPresent
    global typingTaskPresent
    global joystickObject
    global joystickAxis
    global experiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global numberOfCircleExits
    global trialScore

    blockNumber += 1
    numberOfTrials = numberOfSingleTaskTrackingTrials

    if isPracticeTrial:
        experiment = "practiceTracking"
        GiveMessageOnScreen(
            "Nur Tracking\n\n"
            "In diesen Durchgängen führst du nur die Tracking Aufgabe aus.\n"
            "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie der Cursor umher wandert.\n"
            "Der Cursor bewegt sich so lange frei herum, bis du ihn bewegst.",
            15)
        numberOfTrials = 2
    else:
        experiment = "singleTaskTracking"
        GiveMessageOnScreen(
            "Nur Tracking\n\n"
            "Nutze die Durchgänge, um die Geschwindigkeit des Cursors einschätzen zu können, \n"
            "aber halte den Cursor innerhalb des Kreises",
            5)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  ###clear all events
        trackerWindowVisible = True
        typingWindowVisible = False
        trackingTaskPresent = True
        typingTaskPresent = False

        trialNumber = trialNumber + 1
        bg = pygame.Surface(ExperimentWindowSize).convert()
        bg.fill(backgroundColorEntireScreen)
        screen.blit(bg , (0, 0))

        startTime = time.time()

        trackingWindowEntryCounter = 0
        typingWindowEntryCounter = 0

        if trackingTaskPresent:
            joystickAxis = (0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                joystickObject = pygame.joystick.Joystick(0)
                joystickObject.init()
            except (pygame.error, NameError):
                pass

            if trackerWindowVisible:
                openTrackerWindow()
            else:
                closeTrackerWindow()

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while ((time.time() - startTime) < maxTrialTimeSingleTracking) and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates

            if trackingTaskPresent:
                drawTrackerWindow()
                drawCursor(0.02)
                writeParticipantDataFile("none", "none")

            pygame.display.flip()

        if not environmentIsRunning:
            writeParticipantDataFile("trialEnvironmentRunning", "none")
        else:
            writeParticipantDataFile("trialEnvironmentStopped", "none")


def runDualTaskTrials(isPracticeTrial):
    print("FUNCTION: " + getFunctionName())
    global screen
    global maxTrialTimeDual
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global joystickObject
    global joystickAxis
    global experiment
    global blockNumber
    global trialNumber
    global trackerWindowVisible
    global typingWindowVisible
    global availableTypingTaskNumbers
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global incorrectDigits
    global trialScore
    global outsideRadius
    global numberOfCircleExits
    global correctlyTypedDigitsInVisit
    global visitStartTime
    global visitEndTime

    blockNumber += 1

    numberOfTrials = numberOfDualTaskTrials

    if isPracticeTrial:
        maxTrialTimeDual = 120
        experiment = "practiceDualTask"
        GiveMessageOnScreen(
            "Tracking + Tippen\n\n"
            "Du führst jetzt beide Aufgaben gleichzeitig aus.\n"
            "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n"
            "Drücke den Schalter unter deinem Zeigefinger am Joystick, um die Trackingaufgabe zu kontrollieren.\n"
            "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n"
            "Du kannst immer nur eine Aufgabe bearbeiten.", 15)
        GiveMessageOnScreen("Dein Ziel:\n"
                            "Kopiere die Ziffern so schnell wie möglich (so gewinnst du Punkte),\n"
                            "aber halte den Cursor innerhalb des Kreises (sonst verlierst du Punkte)\n"
                            "Fehler beim Tippen führen auch zu einem Punktverlust", 10)

        numberOfTrials = 2
    else:
        maxTrialTimeDual = 120
        experiment = "dualTask"
        GiveMessageOnScreen("Tracking + Tippen\n\n"
                            "Kopiere die Ziffern so schnell wie möglich (so gewinnst du Punkte),\n"
                            "aber halte den Cursor innerhalb des Kreises (sonst verlierst du Punkte).\n"
                            "Fehler beim Tippen führen auch zu einem Punktverlust.\n\n"
                            "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl.", 18)
        GiveMessageOnScreen("Der Cursor bewegt sich mit derselben Geschwindigkeit wie zuvor.\n"
                            "Der Kreis hat dieselbe Größe\n\n"
                            "Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                            "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                            "Du kannst immer nur eine Aufgabe bearbeiten.", 15)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        outsideRadius = False
        correctlyTypedDigitsInVisit = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events

        trackerWindowVisible = False
        typingWindowVisible = True
        trackingTaskPresent = True
        typingTaskPresent = True

        trackingWindowEntryCounter = 0
        typingWindowEntryCounter = 0
        trialNumber = trialNumber + 1

        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        startTime = time.time()

        if trackingTaskPresent:
            joystickAxis = (0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                joystickObject = pygame.joystick.Joystick(0)
                joystickObject.init()
            except (pygame.error, NameError):
                pass

            if trackerWindowVisible:
                openTrackerWindow()
            else:
                closeTrackerWindow()

        if typingTaskPresent:
            generateTypingTaskNumber()
            enteredDigitsStr = ""
            digitPressTimes = [startTime]
            if typingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeParticipantDataFile("trialStart", "none")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (time.time() - startTime) < maxTrialTimeDual and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates
            if trackingTaskPresent:
                drawTrackerWindow()
                drawCursor(0.02)
                writeParticipantDataFile("none", "none")
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

    f = open('participantConditions.csv', 'r')
    individualLines = f.read().split('\n')  ## read by lines
    lines = list(map(lambda x: x.split(';'), individualLines))  # split all elements
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

    fileName = "participant_" + subjNrStr + "_data_" + timestamp + ".csv"
    outputFile = open(fileName, 'w')  # contains the user data
    outputText = "SubjectNr;" \
                 "CurrentTime;" \
                 "TrialTime;" \
                 "BlockNumber;" \
                 "TrialNumber;" \
                 "Experiment;" \
                 "TrackingTaskPresent;" \
                 "TypingTaskPresent;" \
                 "TrackerWindowVisible;" \
                 "TypingWindowVisible;" \
                 "TrackingWindowEntryCounter;" \
                 "TypingWindowEntryCounter;" \
                 "RadiusCircle;" \
                 "StandardDeviationOfNoise;" \
                 "CursorCoordinatesX;" \
                 "CursorCoordinatesY;" \
                 "JoystickAxisX;" \
                 "JoystickAxisY;" \
                 "EnteredDigits;" \
                 "GeneratedTypingTaskNumbers;" \
                 "EnteredDigitsLength;" \
                 "GeneratedTypingTaskNumberLength;" \
                 "NumberOfCircleExits;" \
                 "trialScore;" \
                 "EventMessage1;" \
                 "EventMessage2" + "\n"
    outputFile.write(outputText)

    ########################Second Output File######################################

    summaryFileName = "participant_" + subjNrStr + "_summary_" + timestamp + ".csv"
    summaryOutputFile = open(summaryFileName, 'w')  # contains the user data
    summaryOutputText = "SubjectNr;" \
                        "BlockNumber;" \
                        "TrialNumber;" \
                        "Experiment;" \
                        "StandardDeviationOfNoise;" \
                        "VisitTime;" \
                        "CorrectlyTypedDigitsInVisit;" \
                        "IncorrectlyTypedDigitsInVisit;" \
                        "VisitScore;" \
                        "OutsideRadius" + "\n"
    summaryOutputFile.write(summaryOutputText)


def main():
    global screen
    global environmentIsRunning  # variable that states that there is a main window
    global conditions
    global radiusCircle
    global availableTypingTaskNumbers
    global scoresForPayment
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment
    global penalty
    global currentCondition
    global subjNr
    global startTime
    global fullscreen

    subjNrStr = input("Please enter the subject number here: ")
    subjNr = int(subjNrStr)
    firstTrial = input("First trial? (yes/no) ")
    showPrecedingPenaltyInfo = input("Show penalty and noise information before the experiment starts? (yes/no) ")
    readInputAndCreateOutputFiles(subjNrStr)
    timeOfCompleteStartOfExperiment = time.time()

    pygame.init()
    if fullscreen:
        screen = pygame.display.set_mode(ExperimentWindowSize, pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(ExperimentWindowSize)
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
            radiusCircle = 80
        elif currentCondition[1] == "B":
            radiusCircle = 120
        else:
            raise Exception("Invalid radius " + currentCondition[1])

        # set of digits is 1-9 (9) or 1-3 (3)
        if currentCondition[2] == "9":
            availableTypingTaskNumbers = "123456789"
        elif currentCondition[2] == "3":
            availableTypingTaskNumbers = "123123123"
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
            "radiusCircle": radiusCircle,
            "availableTypingTaskNumbers": availableTypingTaskNumbers,
            "penalty": penalty,
            "penaltyMsg": penaltyMsg
        })

    if firstTrial == "yes":
        GiveMessageOnScreen("Willkommen zum Experiment!\n\n\n"
                            "Wir beginnen mit 3 Probedurchläufen.", 10)
        availableTypingTaskNumbers = "123123123"
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
        radiusCircle = condition["radiusCircle"]
        availableTypingTaskNumbers = condition["availableTypingTaskNumbers"]
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

    GiveMessageOnScreen("Dies ist das Ende der Studie.", 10)
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


