# coding=utf-8
#############################
#  Multitasking experiment: Typing digits (keyboard) while tracking (joystick)
#  Developed by Dietmar Sach (dsach@mail.de) for the Institute of Sport Science of the University of Augsburg
#  Based on a script made by Christian P. Janssen, c.janssen@ucl.ac.uk December 2009 - March 2010
#############################
import inspect
import os
import random
import sys
import time
import traceback
import math
import pygame
import scipy
import scipy.special
import datetime
from enum import Enum


class TaskTypes(Enum):
    """
    Used to represent different task types. Do not change this class.
    """
    SingleTracking = 1
    SingleTyping = 2
    DualTask = 3
    PracticeSingleTracking = 4
    PracticeSingleTyping = 5
    PracticeDualTask = 6


class Block:
    """
    Used to represent a block of trials. Do not change this class.
    """
    TaskType = None
    NumberOfTrials = 0
    def __init__(self, taskType, numberOfTrials):
        self.TaskType = taskType
        self.NumberOfTrials = numberOfTrials


class GeneralExperimentSettings:
    """
    These settings can be modified by the Experiment supervisor
    """
    # Specify radius sizes in ascending order from left to right
    CircleRadiiSmall = [40, 60, 80]
    CircleRadiiBig = [80, 100, 120]
    CircleRadiiPractice = [80, 100, 120]
    TypingTaskNumbersDualTask = ["12", "34", "56"]  # each entry corresponds to an circle radius
    # Each line specifies the inner and outer circle color for the radii above from left to right
    CircleRadiiColors = [{'innerCircleColor': (255, 204, 102), 'borderColor': (255, 0, 0)},  # first radius colors (orange, red)
                         {'innerCircleColor': (252, 215, 141), 'borderColor': (255, 0, 0)},  # second radius colors
                         {'innerCircleColor': (250, 228, 185), 'borderColor': (255, 0, 0)}]  # third radius colors
    CircleBorderThickness = 5
    TypingTaskNumbersSingleTask = "123"
    TypingTaskNumbersCount = 27

    # Set to True if for DualTasks, both Tracking and Typing shall be visible simultaneously
    ParallelDualTasks = True

    # Configure here the order of blocks and the number for trials for each respective. The order is from top to bottom. Also add Practice Tasks here. Use the names from class TaskTypes.
    RunningOrder = [
        Block(taskType=TaskTypes.PracticeSingleTracking, numberOfTrials=2),
        Block(taskType=TaskTypes.PracticeSingleTyping, numberOfTrials=2),
        Block(taskType=TaskTypes.PracticeDualTask, numberOfTrials=2),
        Block(taskType=TaskTypes.SingleTracking, numberOfTrials=1),
        Block(taskType=TaskTypes.SingleTyping, numberOfTrials=1),
        Block(taskType=TaskTypes.DualTask, numberOfTrials=3)
    ]
    MaxTrialTimeDual = 90  # maximum time for dual-task trials
    MaxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
    MaxTrialTimeSingleTyping = 20  # maximum time for single-task typing


class RuntimeExperimentVariables:
    """
    These variables are required by the program itself, do not modify anything here!
    """
    CircleRadii = []  # is set for each condition
    CurrentTypingTaskNumbers = ""
    CurrentTask = None


incorrectlyTypedDigitsTrial = 0
trialScore = 0
IsOutsideRadius = False
correctlyTypedDigitsVisit = 0
incorrectlyTypedDigitsVisit = 0
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
global outputDataFile
global outputDataFileTrialEnd
global conditions
conditions = ()
joystickAxis = (0, 0)  # the motion of the joystick
digitPressTimes = []
startTime = time.time()
timeFeedbackIsShown = 4

backgroundColorTrackingScreen = (255, 255, 255)  # white
backgroundColorDigitScreen = backgroundColorTrackingScreen
backgroundColorEntireScreen = (50, 50, 50)  # gray
coverUpColor = (200, 200, 200)  # very light gray
cursorColor = (0, 0, 255)  # blue

ExperimentWindowSize = (1280, 1024)
taskWindowSize = (450, 450)
cursorSize = (20, 20)

spaceBetweenWindows = 128
offsetLeftRight = int((ExperimentWindowSize[0] - spaceBetweenWindows - 2 * taskWindowSize[0]) / 2)
topLeftCornerOfTypingTaskWindow = (offsetLeftRight, 50)
topLeftCornerOfTrackingTaskWindow = (offsetLeftRight + taskWindowSize[0] + spaceBetweenWindows, 50)

topLeftCornerOfTypingTaskNumber = (taskWindowSize[0] / 2 - 150 + topLeftCornerOfTypingTaskWindow[0],
                                   taskWindowSize[1] / 2 - 20 + topLeftCornerOfTypingTaskWindow[1])

enteredDigitsStr = ""

trackingWindowMiddleX = topLeftCornerOfTrackingTaskWindow[0] + int(taskWindowSize[0] / 2.0)
trackingWindowMiddleY = topLeftCornerOfTrackingTaskWindow[1] + int(taskWindowSize[1] / 2.0)

cursorCoordinates = (trackingWindowMiddleX, trackingWindowMiddleY)

fontsizeGoalAndTypingTaskNumber = 30

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

global trackingWindowVisible
trackingWindowVisible = True
global typingWindowVisible
typingWindowVisible = True

circleRadii = []
standardDeviationOfNoise = -1
stepSizeOfTrackingScreenUpdate = 0.005  # how many seconds does it take for a screen update?
scoresForPayment = []
baseratePayment = 0
maxPayment = 15  # what do we pay maximum?
timeOfCompleteStartOfExperiment = 0  # this value is needed because otherwise one of the time output numbers becomes too large to have enough precision

cursorDistancesToMiddle = []

global lengthOfPathTracked
lengthOfPathTracked = 0


def writeOutputDataFile(eventMessage1, eventMessage2, endOfTrial=False):
    global outputDataFile
    global outputDataFileTrialEnd
    global subjNr
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global blockNumber
    global trialNumber
    global cursorCoordinates
    global joystickAxis
    global trackingWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment  # time at which RuntimeExperimentVariables.CurrentTask started
    global numberOfCircleExits
    global visitScore
    global trialScore
    global correctlyTypedDigitsVisit
    global incorrectlyTypedDigitsTrial
    global incorrectlyTypedDigitsVisit
    global lengthOfPathTracked

    currentTime = time.time() - timeOfCompleteStartOfExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracking)
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
        outputEnteredDigitsLength = len(enteredDigitsStr)
        outputGeneratedTypingTaskNumbers = RuntimeExperimentVariables.CurrentTypingTaskNumbers
        outputGeneratedTypingTaskNumbersLength = len(RuntimeExperimentVariables.CurrentTypingTaskNumbers)
    else:
        outputEnteredDigitsStr = "-"
        outputEnteredDigitsLength = "-"
        outputGeneratedTypingTaskNumbers = "-"
        outputGeneratedTypingTaskNumbersLength = "-"

    if RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask:
        visitTime = time.time() - visitStartTime
    else:
        visitTime = "-"

    currentTask = str(RuntimeExperimentVariables.CurrentTask);

    outputText = \
        str(subjNr) + ";" + \
        str(RuntimeExperimentVariables.CircleRadii) + ";" + \
        str(standardDeviationOfNoise) + ";" + \
        str(currentTime) + ";" + \
        str(trialTime) + ";" + \
        str(visitTime) + ";" + \
        str(blockNumber) + ";" + \
        str(trialNumber) + ";" + \
        str(currentTask) + ";" + \
        str(trackingTaskPresent) + ";" + \
        str(typingTaskPresent) + ";" + \
        str(trackingWindowVisible) + ";" + \
        str(typingWindowVisible) + ";" + \
        str(trackingWindowEntryCounter) + ";" + \
        str(typingWindowEntryCounter) + ";" + \
        str(calculateRmse(clearDistances=endOfTrial)) + ";" + \
        str(lengthOfPathTracked) + ";" + \
        str(outputCursorCoordinateX) + ";" + \
        str(outputCursorCoordinateY) + ";" + \
        str(outputJoystickAxisX) + ";" + \
        str(outputJoystickAxisY) + ";" + \
        str(outputEnteredDigitsStr) + ";" + \
        str(outputEnteredDigitsLength) + ";" + \
        str(outputGeneratedTypingTaskNumbers) + ";" + \
        str(outputGeneratedTypingTaskNumbersLength) + ";" + \
        str(numberOfCircleExits) + ";" + \
        str(trialScore) + ";" + \
        str(visitScore) + ";" + \
        str(correctlyTypedDigitsVisit) + ";" + \
        str(incorrectlyTypedDigitsVisit) + ";" + \
        str(incorrectlyTypedDigitsTrial) + ";" + \
        str(IsOutsideRadius) + ";" + \
        str(eventMessage1) + ";" + \
        str(eventMessage2) + "\n"

    if endOfTrial:
        outputDataFileTrialEnd.write(outputText)
        outputDataFileTrialEnd.flush()
        # typically the above line would do. however this is used to ensure that the file is written
        os.fsync(outputDataFileTrialEnd.fileno())

    outputDataFile.write(outputText)
    outputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(outputDataFile.fileno())


def calculateRmse(clearDistances):
    """
    The distances are collected each time the cursor changes its position.
    The distances are collected until the RMSE is calculated.
    The RMSE is calculated every time the data file is written.
    The distances are cleared if the parameter is set to True
    """
    global cursorDistancesToMiddle

    n = len(cursorDistancesToMiddle)
    if n == 0:
        return 0
    square = 0

    # Calculate square
    for i in range(0, n):
        square += (cursorDistancesToMiddle[i] ** 2)

    if clearDistances:
        cursorDistancesToMiddle = []

    # Calculate Mean
    mean = (square / float(n))
    # Calculate Root
    root = math.sqrt(mean)
    return root


def checkMouseClicked():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            posString = str(pos[0]) + "_" + str(pos[1])
            writeOutputDataFile("MousePressed", posString)
            return pos[0], pos[1]
    return False


def checkKeyPressed():
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global joystickObject  # the joystick object
    global joystickAxis
    global taskWindowSize
    global incorrectlyTypedDigitsTrial
    global correctlyTypedDigitsVisit
    global incorrectlyTypedDigitsVisit
    global cursorCoordinates
    global typingTaskPresent
    global trackingTaskPresent
    global trackingWindowVisible
    global IsOutsideRadius

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and trackingWindowVisible:
            pos = pygame.mouse.get_pos()
            cursorCoordinates = pos[0], pos[1]
        elif event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.JOYAXISMOTION:
            if trackingTaskPresent:
                # values between -1 and 1. (-1,-1) top left corner, (1,-1) top right; (-1,1) bottom left, (1,1) bottom right
                # prevent the program crashing when no joystick is connected
                try:
                    joystickAxis = (joystickObject.get_axis(0), joystickObject.get_axis(1))
                except (pygame.error, NameError):
                    pass
        elif event.type == pygame.JOYBUTTONUP and not GeneralExperimentSettings.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("closeTracking")
                writeOutputDataFile("ButtonRelease", "-")
        elif event.type == pygame.JOYBUTTONDOWN and not GeneralExperimentSettings.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1 and trackingWindowVisible and typingTaskPresent and not GeneralExperimentSettings.ParallelDualTasks:
                print("PRESSED F1 CLOSE TRACKING")
                switchWindows("closeTracking")
                writeOutputDataFile("ButtonRelease", "-")
            elif event.key == pygame.K_F1 and typingWindowVisible and trackingTaskPresent and not GeneralExperimentSettings.ParallelDualTasks:
                print("PRESSED F1 OPEN TRACKING")
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

            if event.key == pygame.K_F4:
                quitApp("F4 was typed to terminate the app")

            # only process keypresses if the digit task is present
            if typingTaskPresent and typingWindowVisible:
                key = event.unicode
                digitPressTimes.append(time.time())

                # In parallel dual task, e is to be typed when the cursor was outside the circle. On e, all key presses are neither correct or incorrect.
                if RuntimeExperimentVariables.CurrentTypingTaskNumbers[0] == "e" and GeneralExperimentSettings.ParallelDualTasks and (RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask):
                    enteredDigitsStr += key
                    UpdateTypingTaskString(reset=False)  # generate one new character
                    writeOutputDataFile("keypress", key)
                    print(f"Neutral key press: {key}")
                # If key press is correct ...
                elif key == RuntimeExperimentVariables.CurrentTypingTaskNumbers[0]:
                    enteredDigitsStr += key
                    UpdateTypingTaskString(reset=False)  # generate one new character
                    correctlyTypedDigitsVisit += 1
                    writeOutputDataFile("keypress", key)
                    print(f"Correct key press: {key}")
                # If key press is wrong ...
                else:
                    incorrectlyTypedDigitsTrial += 1
                    incorrectlyTypedDigitsVisit += 1
                    writeOutputDataFile("wrongKeypress", key)
                    print(f"Incorrect key press: {key}")

                blockMaskingOldLocation = pygame.Surface((int(taskWindowSize[0] - (topLeftCornerOfTypingTaskNumber[0] - topLeftCornerOfTypingTaskWindow[0])), 100)).convert()
                blockMaskingOldLocation.fill(backgroundColorDigitScreen)
                screen.blit(blockMaskingOldLocation, topLeftCornerOfTypingTaskNumber)
                # then post new message
                f = pygame.font.Font(None, fontsizeGoalAndTypingTaskNumber)
                typingTaskNumberMessage = f.render(RuntimeExperimentVariables.CurrentTypingTaskNumbers, True, (0, 0, 0))
                screen.blit(typingTaskNumberMessage, topLeftCornerOfTypingTaskNumber)
                # display all updates (made using blit) on the screen
                pygame.display.flip()


def switchWindows(message):
    global typingWindowVisible
    print("FUNCTION: " + getFunctionName())

    # switching is only done in dual-task
    if RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask:
        if message == "openTracking":
            if trackingTaskPresent:
                openTrackingWindow()
            if typingWindowVisible and typingTaskPresent:
                closeTypingWindow()
        elif message == "closeTracking":
            if trackingTaskPresent:
                closeTrackingWindow()
            if (not typingWindowVisible) and typingTaskPresent:
                openTypingWindow()

    # display all updates (made using blit) on the screen
    pygame.display.flip()


def printTextOverMultipleLines(text, fontsize, color, location):
    global screen
    pygame.event.clear()
    splittedText = text.split("\n")
    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location[0]
    PositionY = location[1]

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        feedbackmessage = f.render(lines, True, color)
        screen.blit(feedbackmessage, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def GiveCountdownMessageOnScreen(timeMessageIsOnScreen):
    print("FUNCTION: " + getFunctionName())
    global screen

    for i in range(0, timeMessageIsOnScreen):
        # prepare background
        completebg = pygame.Surface(ExperimentWindowSize).convert()
        completebg.fill(backgroundColorEntireScreen)
        screen.blit(completebg, (0, 0))

        messageAreaObject = pygame.Surface((int(ExperimentWindowSize[0] / 5), int(ExperimentWindowSize[1] / 5))).convert()
        messageAreaObject.fill((255, 255, 255))

        topCornerOfMessageArea = (int(ExperimentWindowSize[0] * 2 / 5), int(topLeftCornerOfTypingTaskWindow[1] + 10))
        screen.blit(messageAreaObject, topCornerOfMessageArea)

        message = "Mach dich bereit!\n\n" \
                  "            " + str(timeMessageIsOnScreen - i)

        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 45, topCornerOfMessageArea[1] + 10)

        pygame.display.flip()
        printTextOverMultipleLines(message, fontsize, color, location)

        pygame.display.flip()
        time.sleep(1)


def DisplayMessage(message, timeMessageIsOnScreen):
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

    fontsize = fontsizeGoalAndTypingTaskNumber
    color = (0, 0, 0)
    location = (topCornerOfMessageArea[0] + 75, topCornerOfMessageArea[1] + 75)

    printTextOverMultipleLines(message, fontsize, color, location)

    pygame.display.flip()
    time.sleep(timeMessageIsOnScreen)


def drawCanvas():
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
    global scoresForPayment
    global incorrectlyTypedDigitsTrial
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
    scoreForLogging = "-"  # score that's logged
    scoresOnThisBlock = []  # stores the scores on the current block. Can be used to report performance each 5th trial

    if RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask:
        feedbackScore = trialScore
        if trialScore > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        scoresForPayment.append(trialScore)
        scoresOnThisBlock.append(trialScore)  # store score, so average performance can be reported
        scoreForLogging = trialScore

    elif RuntimeExperimentVariables.CurrentTask == TaskTypes.SingleTyping:
        feedbackText = "Anzahl Fehler: \n"
        if typingTaskPresent:
            digitScore = digitPressTimes[-1] - digitPressTimes[0]
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText += "\n\n" + str(incorrectlyTypedDigitsTrial) + " Fehler"
            scoresOnThisBlock.append(incorrectlyTypedDigitsTrial)
            scoreForLogging = digitScore

    if feedbackText != "":
        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)
        printTextOverMultipleLines(feedbackText, fontsize, color, location)

    pygame.display.flip()
    writeOutputDataFile("scoreGiven", str(scoreForLogging))
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

        if RuntimeExperimentVariables.CurrentTask == TaskTypes.SingleTracking:
            feedbackText2 = feedbackText2 + " pixels"
        elif RuntimeExperimentVariables.CurrentTask == TaskTypes.SingleTyping:
            feedbackText2 = feedbackText2 + " errors"
        elif RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask:
            feedbackText2 = "Block " + str(int(len(
                scoresOnThisBlock) / 3)) + " von 6 vollständig. Deine durchschnittliche Leistung der letzten 4 Durchgänge:\n\n" \
                            + str(meanscore) + " points"

        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (topCornerOfMessageArea[0] + 50, topCornerOfMessageArea[1] + 50)

        printTextOverMultipleLines(feedbackText2, fontsize, color, location)
        pygame.display.flip()

        writeOutputDataFile("avscoreGiven", str(meanscore))
        time.sleep(20)


def UpdateTypingTaskString(reset=False):
    """
    Updates the typing task number string.
    :param reset: Set to True if you want to generate a completely new string
    """
    if reset:
        RuntimeExperimentVariables.CurrentTypingTaskNumbers = ""
    # Remove the leftmost character
    RuntimeExperimentVariables.CurrentTypingTaskNumbers = RuntimeExperimentVariables.CurrentTypingTaskNumbers[1:]
    # Generate random characters until the string is complete
    numberOfNewCharacters = GeneralExperimentSettings.TypingTaskNumbersCount - len(RuntimeExperimentVariables.CurrentTypingTaskNumbers)
    if numberOfNewCharacters > 0:
        newCharacters = GetTypingTaskNumbers(numberOfNewCharacters)
        # Update the typing task string. Append the new numbers on the right hand side.
        RuntimeExperimentVariables.CurrentTypingTaskNumbers += newCharacters


def GetTypingTaskNumbers(count):
    """
    Returns a random string of characters that are used in the typing task string, depending on the cursor position.
    Returns e if the cursor is outside of the circle.
    :param count: Specifies how many numbers you want
    :return: A string with <count> numbers
    """
    print("FUNCTION: " + getFunctionName())
    global cursorCoordinates
    global trackingWindowMiddleX
    global trackingWindowMiddleY
    global trackingWindowVisible
    global typingWindowVisible

    # For single typing task only, return the single task string
    if typingWindowVisible and not trackingWindowVisible:
        return ''.join([random.choice(GeneralExperimentSettings.TypingTaskNumbersSingleTask) for _ in range(count)])

    # For dual task with both tracking and typing window visible, determine the typing string from the cursor position
    distanceCursorMiddle = math.sqrt((abs(trackingWindowMiddleX - cursorCoordinates[0])) ** 2 + (abs(trackingWindowMiddleY - cursorCoordinates[1])) ** 2)
    possibleCharacters = None
    for i in range(0, len(RuntimeExperimentVariables.CircleRadii)):
        if distanceCursorMiddle < RuntimeExperimentVariables.CircleRadii[i]:
            possibleCharacters = GeneralExperimentSettings.TypingTaskNumbersDualTask[i]
            break

    # If the cursor is outside the outermost circle radius, the tpying task should show an "e"
    if not possibleCharacters and GeneralExperimentSettings.ParallelDualTasks:
        possibleCharacters = "e"
    elif not possibleCharacters:
        raise Exception("Could not get a random typing task number for the current circle radius!")

    # Return the specified number of random characters
    return ''.join([random.choice(possibleCharacters) for _ in range(count)])


def drawCircles(bg):
    global taskWindowSize
    for i in reversed(range(0, len(RuntimeExperimentVariables.CircleRadii))):
        radiusInnerColor = GeneralExperimentSettings.CircleRadiiColors[i]['innerCircleColor']
        radiusOuterColor = GeneralExperimentSettings.CircleRadiiColors[i]['borderColor']
        radiusCircle = RuntimeExperimentVariables.CircleRadii[i]
        # draw a filled circle
        drawCircle(bg,
                   radiusInnerColor,
                   radiusCircle,
                   0)
        # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size.
        #  The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.
        drawCircle(bg,
                   radiusOuterColor,
                   radiusCircle,
                   GeneralExperimentSettings.CircleBorderThickness)


def drawCircle(image, colour, radius, width=0):
    global cursorCoordinates
    origin = (int(taskWindowSize[0] / 2), int(taskWindowSize[1] / 2))
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
    global joystickAxis
    global trackingWindowVisible
    global stepSizeOfTrackingScreenUpdate
    global IsOutsideRadius
    global cursorColor
    global trackingWindowMiddleX
    global trackingWindowMiddleY
    global taskWindowSize
    global lengthOfPathTracked

    x = cursorCoordinates[0]
    y = cursorCoordinates[1]
    oldX = x
    oldY = y
    final_x = x
    final_y = y

    # only add noise if tracking is not moving
    motionThreshold = 0.08

    joystickAxisWithinThreshold = joystickAxis[0] > motionThreshold or \
                                  joystickAxis[0] < -motionThreshold or \
                                  joystickAxis[1] > motionThreshold or \
                                  joystickAxis[1] < -motionThreshold

    if not (trackingWindowVisible and joystickAxisWithinThreshold):
        final_x = x + random.gauss(0, standardDeviationOfNoise)
        final_y = y + random.gauss(0, standardDeviationOfNoise)

    if trackingWindowVisible:  # only add joystickAxis if the window is open (i.e., if the participant sees what way cursor moves!)
        final_x += joystickAxis[0] * scalingJoystickAxis
        final_y += joystickAxis[1] * scalingJoystickAxis

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)
    nrUpdates = int(sleepTime / stepSizeOfTrackingScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if trackingWindowVisible:
        for i in range(0, nrUpdates):
            x += delta_x
            y += delta_y

            if (x, y) != cursorCoordinates:
                # now check if the cursor is still within screen range
                if x < (topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2
                elif x > (topLeftCornerOfTrackingTaskWindow[0] + taskWindowSize[0] - cursorSize[0] / 2):
                    x = topLeftCornerOfTrackingTaskWindow[0] + taskWindowSize[0] - cursorSize[0] / 2

                if y < (topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2
                elif y > (topLeftCornerOfTrackingTaskWindow[1] + taskWindowSize[1] - cursorSize[1] / 2):
                    y = topLeftCornerOfTrackingTaskWindow[1] + taskWindowSize[1] - cursorSize[1] / 2

                if trackingWindowVisible:  # only update screen when it's visible
                    # now prepare the screen for an update
                    oldLocationX = cursorCoordinates[0] - cursorSize[0] / 2
                    oldLocationY = cursorCoordinates[1] - cursorSize[1] / 2  # gives top-left corner of block
                    blockMaskingOldLocation = pygame.Surface(cursorSize).convert()
                    blockMaskingOldLocation.fill(backgroundColorTrackingScreen)
                    screen.blit(blockMaskingOldLocation, (oldLocationX, oldLocationY))

                    distanceCursorMiddle = math.sqrt((abs(trackingWindowMiddleX - x)) ** 2 + (abs(trackingWindowMiddleY - y)) ** 2)
                    largestCircleRadius = max(RuntimeExperimentVariables.CircleRadii)
                    if distanceCursorMiddle > largestCircleRadius:
                        IsOutsideRadius = True
                        cursorColor = (255, 0, 0)  # red
                    else:
                        IsOutsideRadius = False
                        cursorColor = (0, 0, 255)  # blue

                    # if cursor used to be within radius from target, redraw circle
                    # taskWindowSize = (int(largestCircleRadius * 2.5), int(largestCircleRadius * 2.5))
                    taskWindow = pygame.Surface(taskWindowSize).convert()
                    taskWindow.fill(backgroundColorTrackingScreen)

                    drawCircles(taskWindow)

                    # make area about 30 away from centre
                    screen.blit(taskWindow, (
                        (topLeftCornerOfTrackingTaskWindow[0] + taskWindowSize[0] / 2 - taskWindowSize[0] / 2),
                        (topLeftCornerOfTrackingTaskWindow[1] + taskWindowSize[1] / 2 - taskWindowSize[1] / 2)
                    ))

                    # always redraw cursor
                    newLocation = (x - cursorSize[0] / 2, y - cursorSize[1] / 2)
                    blockAtNewLocation = pygame.Surface(cursorSize).convert()
                    blockAtNewLocation.fill(cursorColor)

                    # blit puts something new on the screen  (should not contain too much info!!)
                    screen.blit(blockAtNewLocation, newLocation)

            # always update coordinates
            cursorCoordinates = (x, y)
            #pygame.display.flip()
            time.sleep(stepSizeOfTrackingScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % stepSizeOfTrackingScreenUpdate
        if mods != 0:
            time.sleep(mods)

    # if tracking window is not visible, just update the values
    else:
        x = final_x
        y = final_y

        # now check if the cursor is still within screen range
        if (x, y) != cursorCoordinates:
            if x < (topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + cursorSize[0] / 2
            elif x > (topLeftCornerOfTrackingTaskWindow[0] + taskWindowSize[0] - cursorSize[0] / 2):
                x = topLeftCornerOfTrackingTaskWindow[0] + taskWindowSize[0] - cursorSize[0] / 2

            if y < (topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + cursorSize[1] / 2
            elif y > (topLeftCornerOfTrackingTaskWindow[1] + taskWindowSize[1] - cursorSize[1] / 2):
                y = topLeftCornerOfTrackingTaskWindow[1] + taskWindowSize[1] - cursorSize[1] / 2
        # if display is not updated, sleep for entire time
        time.sleep(sleepTime)

    # always update coordinates
    cursorCoordinates = (x, y)

    # collect distances of the cursor to the circle middle for the RMSE
    cursorDistancesToMiddle.append(math.sqrt((trackingWindowMiddleX - x) ** 2 + (trackingWindowMiddleY - y) ** 2))

    # collect cumulatively the distance the cursor has moved
    lengthOfPathTracked += math.sqrt((oldX - x) ** 2 + (oldY - y) ** 2)


def closeTypingWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global typingWindowVisible
    global visitEndTime

    typingWindowVisible = False
    visitEndTime = time.time()


def drawCover(window):
    if window == "typing":
        location = topLeftCornerOfTypingTaskWindow
    elif window == "tracking":
        location = topLeftCornerOfTrackingTaskWindow
    else:
        raise Exception("invalid window side specified")

    # draw background
    bg = pygame.Surface(taskWindowSize).convert()
    bg.fill(coverUpColor)
    screen.blit(bg, location)  # make area about 30 away from centre


def openTypingWindow():
    print("FUNCTION: " + getFunctionName())
    global typingWindowVisible
    global typingWindowEntryCounter
    global IsOutsideRadius
    global correctlyTypedDigitsVisit
    global incorrectlyTypedDigitsVisit
    global visitStartTime

    visitStartTime = time.time()
    IsOutsideRadius = False
    correctlyTypedDigitsVisit = 0
    incorrectlyTypedDigitsVisit = 0
    typingWindowEntryCounter = typingWindowEntryCounter + 1
    drawTypingWindow()
    typingWindowVisible = True


def drawTypingWindow():
    global screen

    # draw background
    bg = pygame.Surface(taskWindowSize).convert()
    bg.fill((255, 255, 255))
    screen.blit(bg, topLeftCornerOfTypingTaskWindow)  # make area about 30 away from centre

    if not GeneralExperimentSettings.ParallelDualTasks and (RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask):
        drawCover("tracking")

    f = pygame.font.Font(None, fontsizeGoalAndTypingTaskNumber)
    typingTaskNumberMessage = f.render(RuntimeExperimentVariables.CurrentTypingTaskNumbers, True, (0, 0, 0))
    screen.blit(typingTaskNumberMessage, topLeftCornerOfTypingTaskNumber)


def closeTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    global screen
    global trackingWindowVisible
    global visitEndTime

    trackingWindowVisible = False
    visitEndTime = time.time()


def openTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    global trackingWindowVisible
    global trackingWindowEntryCounter
    global joystickAxis
    global visitScore
    global visitStartTime

    visitStartTime = time.time()
    trackingWindowEntryCounter += 1

    if RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask:
        updateScore()

    drawTrackingWindow()

    trackingWindowVisible = True

    # get the cursor angle
    # prevent the program crashing when no joystick is connected
    try:
        joystickAxis = (joystickObject.get_axis(0), joystickObject.get_axis(1))
    except (pygame.error, NameError):
        pass


def drawTrackingWindow():
    global screen
    global cursorColor
    global cursorCoordinates
    global penalty

    # draw background
    bg = pygame.Surface(taskWindowSize).convert()
    bg.fill(backgroundColorTrackingScreen)
    drawCircles(bg)
    screen.blit(bg, topLeftCornerOfTrackingTaskWindow)  # make area about 30 away from centre
    newCursorLocation = (cursorCoordinates[0] - (cursorSize[0] / 2), cursorCoordinates[1] - (cursorSize[1] / 2))
    newCursor = pygame.Surface(cursorSize).convert()
    newCursor.fill(cursorColor)
    screen.blit(newCursor, newCursorLocation)  # blit puts something new on the screen

    # Show the number of points above the tracking circle
    if penalty != "none" and (RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask) and not GeneralExperimentSettings.ParallelDualTasks:
        intermediateMessage = str(visitScore) + " Punkte"
        fontsize = fontsizeGoalAndTypingTaskNumber
        color = (0, 0, 0)
        location = (900, 65)
        printTextOverMultipleLines(intermediateMessage, fontsize, color, location)

    if not GeneralExperimentSettings.ParallelDualTasks and (RuntimeExperimentVariables.CurrentTask == TaskTypes.DualTask or RuntimeExperimentVariables.CurrentTask == TaskTypes.PracticeDualTask):
        drawCover("typing")

    # display all updates (made using blit) on the screen
    pygame.display.flip()


def updateScore():
    print("FUNCTION: " + getFunctionName())
    global trialScore  # cumulative score for the current trial
    global IsOutsideRadius  # boolean - did the cursor leave the circle
    global numberOfCircleExits
    global correctlyTypedDigitsVisit  # number of correctly typed digits
    global incorrectlyTypedDigitsVisit  # number of incorrectly typed digits
    global visitScore  # Score for one visit to the digit window
    global cursorColor
    global penalty

    if penalty == "none":
        visitScore = 0
    elif IsOutsideRadius:
        numberOfCircleExits += 1
        if penalty == "lose500":
            # loose 500
            visitScore = ((correctlyTypedDigitsVisit + 10) + (incorrectlyTypedDigitsVisit - 5)) - 500

        if penalty == "loseAll":
            # loose all
            visitScore = 0

        if penalty == "loseHalf":
            # loose half
            visitScore = 0.5 * ((correctlyTypedDigitsVisit * 10) + (incorrectlyTypedDigitsVisit * -5))  # penalty for exit is to lose half points
    else:
        visitScore = (correctlyTypedDigitsVisit * 10) + (incorrectlyTypedDigitsVisit * -5)  # gain is 10 for correct digit and -5 for incorrect digit

    # add the score for this digit task visit to the overall trial score
    # duringtrial score is used in reportUserScore
    trialScore += visitScore
    writeOutputDataFile("updatedVisitScore", str(visitScore))
    IsOutsideRadius = False


def runSingleTaskTypingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    global screen
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global blockNumber
    global trialNumber
    global trackingWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global numberOfCircleExits
    global trialScore
    global correctlyTypedDigitsVisit
    global incorrectlyTypedDigitsVisit
    global incorrectlyTypedDigitsTrial
    global cursorDistancesToMiddle
    global lengthOfPathTracked

    blockNumber += 1

    if isPracticeTrial:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.PracticeSingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "In diesen Durchgängen übst du nur die Tippaufgabe.\n"
                       "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                       "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren.)", 15)
    else:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.SingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "Kopiere die Ziffern so schnell wie möglich.\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n", 10)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        correctlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsTrial = 0
        cursorDistancesToMiddle = []
        lengthOfPathTracked = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events
        trackingWindowVisible = False
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
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            enteredDigitsStr = ""
            digitPressTimes = [startTime]

            if typingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (time.time() - startTime) < GeneralExperimentSettings.MaxTrialTimeSingleTyping and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates
            pygame.display.flip()
            time.sleep(0.02)

        if (time.time() - startTime) >= GeneralExperimentSettings.MaxTrialTimeSingleTyping:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not environmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def runSingleTaskTrackingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    global screen
    global startTime  # stores time at which trial starts
    global trackingTaskPresent
    global typingTaskPresent
    global joystickObject
    global joystickAxis
    global blockNumber
    global trialNumber
    global trackingWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global numberOfCircleExits
    global trialScore
    global correctlyTypedDigitsVisit
    global incorrectlyTypedDigitsVisit
    global incorrectlyTypedDigitsTrial
    global cursorDistancesToMiddle
    global cursorCoordinates
    global lengthOfPathTracked

    blockNumber += 1

    if isPracticeTrial:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.PracticeSingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "In diesen Durchgängen übst du nur die Trackingaufgabe.\n"
            "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie schnell der blaue Cursor umherwandert.\n"
            "Der Cursor bewegt sich so lange frei herum, bis du ihn mit dem Joystick bewegst.\n"
            "Denk daran: deine Aufgabe ist es, zu verhindern, dass der blaue Cursor den Kreis verlässt!",
            15)
    else:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.SingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "Nutze diesen Durchgang, um dich mit der Geschwindigkeit des Cursors vertraut zu machen, \n"
            "und denk daran den Cursor mit deinem Joystick in der Kreismitte zu halten.",
            10)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()
        trackingWindowVisible = True
        typingWindowVisible = False
        trackingTaskPresent = True
        typingTaskPresent = False
        correctlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsTrial = 0
        cursorDistancesToMiddle = []
        lengthOfPathTracked = 0

        trialNumber = trialNumber + 1
        bg = pygame.Surface(ExperimentWindowSize).convert()
        bg.fill(backgroundColorEntireScreen)
        screen.blit(bg, (0, 0))

        startTime = time.time()

        trackingWindowEntryCounter = 0
        typingWindowEntryCounter = 0
        cursorCoordinates = (trackingWindowMiddleX, trackingWindowMiddleY)

        if trackingTaskPresent:
            joystickAxis = (0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                joystickObject = pygame.joystick.Joystick(0)
                joystickObject.init()
            except (pygame.error, NameError):
                pass

            if trackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        writeOutputDataFile("trialStart", "-")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while ((time.time() - startTime) < GeneralExperimentSettings.MaxTrialTimeSingleTracking) and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates

            if trackingTaskPresent and trackingWindowVisible:
                drawTrackingWindow()
                drawCursor(0.02)
                writeOutputDataFile("trackingVisible", "-")

            pygame.display.flip()

        if not environmentIsRunning:
            writeOutputDataFile("trialEnvironmentRunning", "-", True)
        else:
            writeOutputDataFile("trialEnvironmentStopped", "-", True)


def runDualTaskTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    global screen
    global startTime  # stores time at which trial starts
    global digitPressTimes  # stores the intervals between keypresses
    global enteredDigitsStr
    global trackingTaskPresent
    global typingTaskPresent
    global joystickObject
    global joystickAxis
    global blockNumber
    global trialNumber
    global trackingWindowVisible
    global typingWindowVisible
    global trackingWindowEntryCounter
    global typingWindowEntryCounter
    global trialScore
    global IsOutsideRadius
    global numberOfCircleExits
    global correctlyTypedDigitsVisit
    global visitStartTime
    global visitEndTime
    global incorrectlyTypedDigitsTrial
    global incorrectlyTypedDigitsVisit
    global cursorDistancesToMiddle
    global cursorCoordinates
    global lengthOfPathTracked

    blockNumber += 1

    if isPracticeTrial:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.PracticeDualTask
        message = "Tracking + Tippen (MULTITASKING)\n\n" \
                  "Du übst jetzt beide Aufgaben gleichzeitig!\n\n"
        if not GeneralExperimentSettings.ParallelDualTasks:
            message += "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n" \
                       "Drücke den Schalter unter deinem Zeigefinger am Joystick, um zu kontrollieren ob der blaue Cursor\n" \
                       "noch innerhalb des Kreises ist.\n" \
                       "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n" \
                       "Du kannst immer nur eine Aufgabe bearbeiten."
        DisplayMessage("Dein Ziel:\n\n"
                       "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte,\n"
                       "aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
                       "Fehler beim Tippen führen auch zu Punktverlust.", 10)
    else:
        RuntimeExperimentVariables.CurrentTask = TaskTypes.DualTask
        DisplayMessage("Tracking + Tippen (MULTITASKING)\n\n"
                       "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte,\n"
                       "aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
                       "Fehler beim Tippen führen auch zu einem Punktverlust.\n\n"
                       "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl.", 18)
        if not GeneralExperimentSettings.ParallelDualTasks:
            DisplayMessage("Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                           "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                           "Du kannst immer nur eine Aufgabe bearbeiten.", 15)

    for i in range(0, numberOfTrials):
        numberOfCircleExits = 0
        trialScore = 0
        IsOutsideRadius = False
        correctlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsVisit = 0
        incorrectlyTypedDigitsTrial = 0
        cursorDistancesToMiddle = []
        lengthOfPathTracked = 0

        GiveCountdownMessageOnScreen(3)
        pygame.event.clear()  # clear all events

        if GeneralExperimentSettings.ParallelDualTasks:
            trackingWindowVisible = True
            typingWindowVisible = True
        else:
            trackingWindowVisible = False
            typingWindowVisible = True

        trackingTaskPresent = True
        typingTaskPresent = True

        trackingWindowEntryCounter = 0
        typingWindowEntryCounter = 0
        trialNumber = trialNumber + 1
        cursorCoordinates = (trackingWindowMiddleX, trackingWindowMiddleY)

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

            if trackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        if typingTaskPresent:
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            enteredDigitsStr = ""
            digitPressTimes = [startTime]
            if typingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        # display all updates (made using blit) on the screen
        pygame.display.flip()

        while (time.time() - startTime) < GeneralExperimentSettings.MaxTrialTimeDual and environmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the tracking task and the typingTask and starts relevant display updates

            if trackingTaskPresent and trackingWindowVisible:
                drawTrackingWindow()
                drawCursor(0.02)
            if GeneralExperimentSettings.ParallelDualTasks and typingTaskPresent and typingWindowVisible:
                drawTypingWindow()

            if GeneralExperimentSettings.ParallelDualTasks:
                eventMsg = "trackingAndTypingVisible"
            elif trackingWindowVisible:
                eventMsg = "trackingVisible"
            elif typingWindowVisible:
                eventMsg = "typingVisible"

            writeOutputDataFile(eventMsg, "-")

        visitEndTime = time.time()
        updateScore()

        if (time.time() - startTime) >= GeneralExperimentSettings.MaxTrialTimeDual:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not environmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def initializeOutputFiles(subjNrStr):
    """
    Set the participant condition. Initialize the output files
    """
    global outputDataFile
    global outputDataFileTrialEnd
    outputText = \
        "SubjectNr" + ";" \
        "RadiusCircle" + ";" \
        "StandardDeviationOfNoise" + ";" \
        "CurrentTime" + ";" \
        "TrialTime" + ";" \
        "VisitTime" + ";" \
        "BlockNumber" + ";" \
        "TrialNumber" + ";" \
        "Experiment" + ";" \
        "TrackingTaskPresent" + ";" \
        "TypingTaskPresent" + ";" \
        "TrackingWindowVisible" + ";" \
        "TypingWindowVisible" + ";" \
        "TrackingWindowEntryCounter" + ";" \
        "TypingWindowEntryCounter" + ";" \
        "RMSE" + ";" \
        "LengthPathTrackedPixel" + ";" \
        "CursorCoordinatesX" + ";" \
        "CursorCoordinatesY" + ";" \
        "JoystickAxisX" + ";" \
        "JoystickAxisY" + ";" \
        "EnteredDigits" + ";" \
        "EnteredDigitsLength" + ";" \
        "RuntimeExperimentVariables.CurrentTypingTaskNumbers" + ";" \
        "GeneratedTypingTaskNumberLength" + ";" \
        "NumberOfCircleExits" + ";" \
        "TrialScore" + ";" \
        "VisitScore" + ";" \
        "CorrectDigitsVisit" + ";" \
        "IncorrectDigitsVisit" + ";" \
        "IncorrectDigitsTrial" + ";" \
        "OutsideRadius" + ";" \
        "EventMessage1" + ";" \
        "EventMessage2" + "\n"

    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    dataFileName = "participant_" + subjNrStr + "_data_" + timestamp + ".csv"
    outputDataFile = open(dataFileName, 'w')  # contains the user data
    outputDataFile.write(outputText)
    outputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(outputDataFile.fileno())

    summaryFileName = "participant_" + subjNrStr + "_data_lastTrialEntry_" + timestamp + ".csv"
    outputDataFileTrialEnd = open(summaryFileName, 'w')  # contains the user data
    outputDataFileTrialEnd.write(outputText)
    outputDataFileTrialEnd.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(outputDataFileTrialEnd.fileno())


def readConditionFile(subjNrStr):
    """
    Read the participant file
    """
    global conditions

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


def ShowStartExperimentScreen():
    global startTime
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


def main():
    global screen
    global environmentIsRunning  # variable that states that there is a main window
    global conditions
    global scoresForPayment
    global standardDeviationOfNoise
    global timeOfCompleteStartOfExperiment
    global penalty
    global currentCondition
    global subjNr
    global startTime
    global fullscreen

    ValidateExperimentSettings()

    subjNrStr = input("Please enter the subject number here: ")
    subjNr = int(subjNrStr)

    firstTrialInput = input("First trial? (yes/no) ")
    if firstTrialInput != "yes" and firstTrialInput != "no":
        raise Exception("Invalid input '" + firstTrialInput + "'. Allowed is 'yes' or 'no' only.")

    showPrecedingPenaltyInfo = input("Show reward, penalty and noise information before the experiment starts? (yes/no) ")
    if showPrecedingPenaltyInfo != "yes" and showPrecedingPenaltyInfo != "no":
        raise Exception("Invalid input '" + showPrecedingPenaltyInfo + "'. Allowed is 'yes' or 'no' only.")

    readConditionFile(subjNrStr)
    initializeOutputFiles(subjNrStr)
    timeOfCompleteStartOfExperiment = time.time()

    pygame.init()
    if fullscreen:
        screen = pygame.display.set_mode(ExperimentWindowSize, pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(ExperimentWindowSize)
    pygame.display.set_caption("Multitasking 3.0")
    environmentIsRunning = True

    ShowStartExperimentScreen()

    # verify all conditions before the experiment starts so that the program would crash at the start if it does
    conditionsVerified = []
    for pos in range(0, len(conditions)):
        currentCondition = conditions[pos]
        numDigits = len(currentCondition)
        if numDigits != 3:
            raise Exception("Current Condition" + currentCondition + " has invalid length " + str(len(currentCondition)))

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
            radiusCircle = GeneralExperimentSettings.CircleRadiiSmall
        elif currentCondition[1] == "B":
            radiusCircle = GeneralExperimentSettings.CircleRadiiBig
        else:
            raise Exception("Invalid radius " + currentCondition[1])

        # only if the fourth digit is specified, define penalty
        if currentCondition[2] == "a":
            penalty = "loseAll"
            penaltyMsg = "alle"
        elif currentCondition[2] == "h":
            penalty = "loseHalf"
            penaltyMsg = "die Hälfte deiner"
        elif currentCondition[2] == "n":
            penalty = "lose500"
            penaltyMsg = "500"
        elif currentCondition[2] == "-":
            penalty = "none"
            penaltyMsg = "-"
        else:
            raise Exception("Invalid penalty " + currentCondition[2])

        conditionsVerified.append({
            "standardDeviationOfNoise": standardDeviationOfNoise,
            "noiseMsg": noiseMsg,
            "radiusCircle": radiusCircle,
            "penalty": penalty,
            "penaltyMsg": penaltyMsg
        })

    if firstTrialInput == "yes":
        DisplayMessage("Willkommen zum Experiment!\n\n\n"
                       "Wir beginnen mit den Übungsdurchläufen.", 10)

        # do practice trials
        RuntimeExperimentVariables.CircleRadii = GeneralExperimentSettings.CircleRadiiPractice
        for block in GeneralExperimentSettings.RunningOrder:
            if block.TaskType == TaskTypes.PracticeSingleTracking:
                runSingleTaskTrackingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeSingleTyping:
                runSingleTaskTypingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeDualTask:
                runDualTaskTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)

        DisplayMessage("Nun beginnt der Hauppteil und wir testen deine Leistung in den Aufgaben, die du \n"
                       "gerade geübt hast.\n"
                       "Versuche im Laufe des Experiments so viele Punkte wie möglich zu gewinnen!", 10)

    # main experiment loop with verified conditions
    for condition in conditionsVerified:
        print("condition: " + str(condition))
        # set global and local variables
        standardDeviationOfNoise = condition["standardDeviationOfNoise"]
        noiseMsg = condition["noiseMsg"]
        RuntimeExperimentVariables.CircleRadii = condition["radiusCircle"]
        penalty = condition["penalty"]
        penaltyMsg = condition["penaltyMsg"]

        for block in GeneralExperimentSettings.RunningOrder:
            if block.TaskType == TaskTypes.SingleTracking:
                message = getMessageBeforeTrial(TaskTypes.SingleTracking, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runSingleTaskTrackingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.SingleTyping:
                message = getMessageBeforeTrial(TaskTypes.SingleTyping, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runSingleTaskTypingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.DualTask:
                message = getMessageBeforeTrial(TaskTypes.DualTask, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runDualTaskTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)

        message = "Bisher hast du: " + str(scipy.sum(scoresForPayment)) + " Punkte"
        DisplayMessage(message, 8)

    DisplayMessage("Dies ist das Ende der Studie.", 10)
    quitApp()


def ValidateExperimentSettings():
    """Some important consistency checks for fields of GeneralExperimentSettings"""
    if GeneralExperimentSettings.CircleRadiiSmall != sorted(GeneralExperimentSettings.CircleRadiiSmall):
        quitApp("GeneralExperimentSettings.CircleRadiiSmall is not sorted in ascending order! This must be fixed for the random numbers to work in parallel dual task!")
    if GeneralExperimentSettings.CircleRadiiBig != sorted(GeneralExperimentSettings.CircleRadiiBig):
        quitApp("GeneralExperimentSettings.CircleRadiiBig is not sorted in ascending order! This must be fixed for the random numbers to work in parallel dual task!")
    if len(GeneralExperimentSettings.CircleRadiiSmall) != len(GeneralExperimentSettings.CircleRadiiBig) \
            or len(GeneralExperimentSettings.CircleRadiiBig) != len(GeneralExperimentSettings.CircleRadiiColors) \
            or len(GeneralExperimentSettings.CircleRadiiColors) != len(GeneralExperimentSettings.TypingTaskNumbersDualTask):
        quitApp("Circle radii settings are inconsistent! Make sure the lists all have the same length!")
    for block in GeneralExperimentSettings.RunningOrder:
        if block.TaskType.name not in TaskTypes._member_names_:
            quitApp(f"Specified TaskType {block.TaskType} is invalid!")


def getMessageBeforeTrial(trialType, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo):
    message = "NEUER BLOCK: \n\n\n"
    if trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask:
        message += "In den folgenden Durchgängen bewegt sich der Cursor mit " + noiseMsg + " Geschwindigkeit. \n"
    if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
        message += "Für jede korrekt eingegebene Ziffer bekommst du 10 Punkte. \n"
    if showPrecedingPenaltyInfo == "yes":
        if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
            message += "Bei jeder falsch eingetippten Ziffer verlierst du 5 Punkte. \n"
        if trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask:
            message += "Achtung: Wenn der Cursor den Kreis verlässt, verlierst du " + penaltyMsg + " deiner Punkte."
    elif showPrecedingPenaltyInfo == "no":
        if trialType == TaskTypes.DualTask:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern und wenn der Punkt den Kreis verlässt."
        elif trialType == TaskTypes.SingleTyping:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern."
        elif trialType == TaskTypes.SingleTracking:
            message += "Achtung: Du verlierst Punkte wenn der Punkt den Kreis verlässt."
    return message


def quitApp(message=None):
    global environmentIsRunning
    global outputDataFile
    global outputDataFileTrialEnd
    if message:
        print(message)
    environmentIsRunning = False
    pygame.display.quit()
    pygame.quit()
    try:
        outputDataFile.close()
        outputDataFileTrialEnd.close()
    except NameError:
        pass
    sys.exit()


def getFunctionName():
    return inspect.stack()[1][3]


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        stack = traceback.format_exc()
        with open("Error_Logfile.txt", "a") as log:
            log.write(f"{datetime.datetime.now()} {str(e)}   {str(stack)} \n")
            print(str(e))
            print(str(stack))
            print("PLEASE CHECK Error_Logfile.txt, the error is logged there!")
